from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import RedirectResponse
import requests
from datetime import date
from typing import Optional
import json

from utils import get_price, get_block_timestamp
from sqlalchemy.orm import Session
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


@app.get('/')
def home():
    return RedirectResponse(url="/docs", status_code=302)


# Endpoint to convert ETH to USDT at given timestamp
def eth_to_usdt(eth_amount, timestamp):
    url = BINANCE_BASE_URL + "klines"
    price = get_price(url, f"ETHUSDT", timestamp)

    if price is not None: return eth_amount * price
    return None


# Endpoint to fetch historical transactions for a given period of time
@app.get('/transactions')
def get_historical_transactions(start_time: Optional[date] = None, end_time: Optional[date] = None):
    params = {
        "module": "account",
        "action": "tokentx",
        "address": CONTRACT_ADDRESS,
        "startblock": start_time,
        "endblock": end_time,
        "sort": "asc",
        "apikey": ETHERSCAN_API_KEY
    }

    response = requests.get(ETHERSCAN_BASE_URL, params=params)
    if response.status_code == 200:
        return response.json()["result"]
    else:
        return None


# Endpoint to get transaction fee for a given transaction hash
@app.get('/transaction')
def get_transaction(transaction_hash: str, db: Session = Depends(get_db)) -> float:
    transaction = crud.get_transaction(db, transaction_hash)
    
    if transaction is not None: return transaction.transaction_fee
    
    params = {
        "module": "proxy",
        "action": "eth_getTransactionReceipt",
        "txhash": transaction_hash,
        "apikey": ETHERSCAN_API_KEY
    }

    response = requests.get(ETHERSCAN_BASE_URL, params=params)
    
    if response.status_code == 200:
        body = response.json()
        if body['result'] is not None:
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
                                                      transaction_fee=transaction_fee_usdt)
            crud.create_transaction(db, transaction_obj)
            
            return transaction_fee_usdt
        
        else: 
            raise HTTPException(status_code=404, detail="Transaction not found")
    
    raise HTTPException(status_code=500, detail="Failed to fetch transaction")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", port=5000, reload=True)