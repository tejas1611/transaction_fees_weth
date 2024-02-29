from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import RedirectResponse
from fastapi_utils.tasks import repeat_every
import requests
from datetime import datetime, timezone
from typing import Optional, List, Dict
import json
from sqlalchemy.orm import Session

from utils import get_price, get_block_timestamp, get_first_block_after_timestamp
import models
import schemas
import crud
from database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

with open('config.json') as config_file:
    config = json.load(config_file)

ETHERSCAN_API_KEY = config["ETHERSCAN_API_KEY"]
CONTRACT_ADDRESS = config["WETH_USDT_CONTRACT_ADDRESS"]
ETHERSCAN_BASE_URL = config["ETHERSCAN_BASE_URL"]
BINANCE_BASE_URL = config["BINANCE_BASE_URL"]

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Endpoint to convert ETH to USDT at given timestamp
def eth_to_usdt(eth_amount, timestamp):
    url = BINANCE_BASE_URL + "klines"
    price = get_price(url, f"ETHUSDT", timestamp)

    if price is not None: return eth_amount * price
    return None


# Root directory redirect to /docs (Swagger)
@app.get('/')
def home():
    return RedirectResponse(url="/docs", status_code=302)


# Endpoint to fetch historical transactions for a given period of time
@app.get('/transactions')
def get_historical_transactions(start_time: datetime, end_time: datetime, db: Session = Depends(get_db)) -> List[Dict]:
    start_ts = int(datetime.timestamp(start_time.replace(tzinfo=timezone.utc)))
    end_ts = int(datetime.timestamp(end_time.replace(tzinfo=timezone.utc))) + 1

    blockno_after_ts = get_first_block_after_timestamp(ETHERSCAN_BASE_URL, ETHERSCAN_API_KEY, start_ts)
    
    transaction_fees_result = []
    transaction_schemas = []
    curr_block = blockno_after_ts
    completed = False

    while not completed:
        params = {
            "module": "account",
            "action": "tokentx",
            "address": CONTRACT_ADDRESS,
            "startblock": curr_block,
            "sort": "asc",
            "apikey": ETHERSCAN_API_KEY
        }

        response = requests.get(ETHERSCAN_BASE_URL, params=params)
        all_transactions = response.json()["result"]

        if response.status_code == 200:
            # Each transaction hash has two entries in the response
            for i in range(0, len(all_transactions), 2):
                transaction = all_transactions[i]
                ts = int(transaction["timeStamp"])
                if ts > end_ts:
                    completed = True
                    break
                else:
                    transaction_hash = transaction["hash"]

                    # Check transaction hash in db
                    transaction_from_db = crud.get_transaction(db, transaction_hash)
                    if transaction_from_db is not None: 
                        transaction_fee_usdt = transaction_from_db.transaction_fee_usdt
                    else:
                        gas_price = int(transaction["gasPrice"])
                        gas_used = int(transaction["gasUsed"])
                        transaction_fee_eth = 1.0 * gas_price * gas_used / 10**18
                        transaction_fee_usdt = eth_to_usdt(transaction_fee_eth, ts)

                        transaction_obj = schemas.TransactionBase(id=transaction_hash,
                                                        timestamp=ts,
                                                        gas_price=gas_price,
                                                        gas_used=gas_used,
                                                        transaction_fee_usdt=transaction_fee_usdt)
                        transaction_schemas.append(transaction_obj)

                    transaction_fees_result.append({"hash": transaction_hash, 
                                                    "timestamp": ts, 
                                                    "transaction_fee_usdt": transaction_fee_usdt})
                
                curr_block = int(transaction["blockNumber"]) + 1
        
        else: break
    
    # Write transactions to db
    if transaction_schemas: crud.create_transactions(db, transaction_schemas)

    return transaction_fees_result


# Endpoint to get transaction fee for a given transaction hash
@app.get('/transaction')
def get_transaction(transaction_hash: str, db: Session = Depends(get_db)) -> float:
    transaction = crud.get_transaction(db, transaction_hash)
    
    if transaction is not None: return transaction.transaction_fee_usdt
    
    params = {
        "module": "proxy",
        "action": "eth_getTransactionReceipt",
        "txhash": transaction_hash,
        "apikey": ETHERSCAN_API_KEY
    }

    response = requests.get(ETHERSCAN_BASE_URL, params=params)
    
    if response.status_code == 200:
        body = response.json()
        if 'result' in body and body['result'] is not None:
            gas_price = int(body['result']['effectiveGasPrice'], 16)
            gas_used = int(body['result']['gasUsed'], 16)
            transaction_fee = gas_price * gas_used

            block_number = body['result']['blockNumber']
            ts = get_block_timestamp(ETHERSCAN_BASE_URL, ETHERSCAN_API_KEY, block_number)

            transaction_fee_eth = 1.0 * transaction_fee / 10**18
            transaction_fee_usdt = eth_to_usdt(transaction_fee_eth, ts)
            
            if transaction_fee_usdt is None:
                raise HTTPException(status_code=500, detail="Failed to fetch price")
            
            transaction_obj = schemas.TransactionBase(id=transaction_hash,
                                                      timestamp=ts,
                                                      gas_price=gas_price,
                                                      gas_used=gas_used,
                                                      transaction_fee_usdt=transaction_fee_usdt)
            crud.create_transaction(db, transaction_obj)
            
            return transaction_fee_usdt
        
        else: 
            raise HTTPException(status_code=404, detail="Transaction not found")
    
    raise HTTPException(status_code=500, detail="Failed to fetch transaction")

# Function to record latest transactions in the database
def record_latest_transactions(start_block):
    latest_blockno = -1
    transaction_schemas = dict()

    # Query ERC-20 Transactions starting from the last recorded block
    params = {
        "module": "account",
        "action": "tokentx",
        "address": CONTRACT_ADDRESS,
        "startblock": start_block,
        "sort": "asc",
        "apikey": ETHERSCAN_API_KEY
    }

    response = requests.get(ETHERSCAN_BASE_URL, params=params)
    all_transactions = response.json()["result"]

    if response.status_code == 200:
        # Each transaction hash has two entries in the response
        for i in range(0, len(all_transactions), 2):
            transaction = all_transactions[i]

            transaction_hash = transaction["hash"]
            ts = int(transaction["timeStamp"])
            gas_price = int(transaction["gasPrice"])
            gas_used = int(transaction["gasUsed"])
            transaction_fee_eth = 1.0 * gas_price * gas_used / 10**18
            
            transaction_fee_usdt = eth_to_usdt(transaction_fee_eth, ts)

            if transaction_fee_usdt is None:
                raise HTTPException(status_code=500, detail="Failed to fetch price")

            transaction_obj = schemas.TransactionBase(id=transaction_hash,
                                            timestamp=ts,
                                            gas_price=gas_price,
                                            gas_used=gas_used,
                                            transaction_fee_usdt=transaction_fee_usdt)
            transaction_schemas[transaction_hash] = transaction_obj
            latest_blockno = int(transaction["blockNumber"]) + 1

    # Write transactions to db
    if transaction_schemas: 
        with SessionLocal() as db:
            crud.create_transactions(db, list(transaction_schemas.values()))
            # print(f"Wrote to db {len(transaction_schemas)} transactions")

    return latest_blockno if latest_blockno != -1 else start_block


# Function that runs every 10 seconds to fetch recent transactions and store them in the database.
# Only record live transactions since startup of server.
last_block_recorded = None
@app.on_event("startup")
@repeat_every(seconds=40, raise_exceptions=True)
def get_recent_transactions() -> None:    
    global last_block_recorded

    if last_block_recorded is None:
        # Get the latest block number
        params = {
            "module": "proxy",
            "action": "eth_blockNumber",
            "apikey": ETHERSCAN_API_KEY
        }
        response = requests.get(ETHERSCAN_BASE_URL, params=params)
        if response.status_code == 200:
            last_block_recorded = int(response.json()["result"], 16)

    try:
        last_block_recorded = record_latest_transactions(last_block_recorded)
    except HTTPException:
        print("Failed to fetch live transactions. Try again later.")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", port=5000, reload=False)