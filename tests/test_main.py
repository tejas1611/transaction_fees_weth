from fastapi.testclient import TestClient

import json
from main import app, eth_to_usdt

client = TestClient(app)

with open('config.json') as config_file:
    config = json.load(config_file)

ETHERSCAN_API_KEY = config["ETHERSCAN_API_KEY"]
CONTRACT_ADDRESS = config["WETH_USDT_CONTRACT_ADDRESS"]
ETHERSCAN_BASE_URL = config["ETHERSCAN_BASE_URL"]
BINANCE_BASE_URL = config["BINANCE_BASE_URL"]


def test_transaction_in_db():
    response = client.get("/transaction",params={"transaction_hash": "0x4809437de726c077dddcd4d8feb0685283baa33966a73dda645a5e32685de090"})
    assert response.status_code == 200
    
    returned_fee = float(response.text)
    true_fee = 42.1309
    assert abs(returned_fee - true_fee) < 0.1

def test_transaction_not_in_db():
    response = client.get("/transaction",params={"transaction_hash": "0x51d4785f112ddc97fe933fdffef54fdaf0eff2544fa5663f93e4ed84d7ad1fae"})
    assert response.status_code == 200
    
    returned_fee = float(response.text)
    true_fee = 137.10
    assert abs(returned_fee - true_fee) < 0.1

def test_eth_to_usdt():
    returned_amount_usdt = eth_to_usdt(1.0, 1620000000)
    true_amount_usdt = 2949.33

    assert returned_amount_usdt is not None
    assert abs(returned_amount_usdt - true_amount_usdt) < 0.1

def test_eth_to_usdt_invalid_timestamp():
    returned_amount_usdt = eth_to_usdt(1.0, 0)
    assert returned_amount_usdt is None

def test_historical_transactions():
    response = client.get("/transactions", params={"start_time": "2022-04-21T19:00:00", "end_time": "2022-04-21T19:02:00"})
    
    assert response.status_code == 200
    transactions = json.loads(response.text)

    true_hashes = set(["0x4809437de726c077dddcd4d8feb0685283baa33966a73dda645a5e32685de090", 
                       "0xaf283b820f536a8b6d654368339bd7b78409d1c9201a5eb400dfadef6469decb",
                       "0x55cc29a32695f3e8d3a4b88ce2f6e3e4779cc89c6ebe97cf505f0c3652aa4acc",
                       "0xd93520e451888e01fab7077eea1aaf40790be49bdd451194143cfca5154fdfb3",
                       "0xd3b239b76a1d9d83b2f25141eabaff2ec3afabdd84abd46405524887a604e154"])
    
    returned_hashes = set([transaction["hash"] for transaction in transactions])

    assert true_hashes == returned_hashes