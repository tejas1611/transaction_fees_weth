import json
from utils import get_block_timestamp, get_first_block_after_timestamp

with open('config.json') as config_file:
    config = json.load(config_file)

ETHERSCAN_API_KEY = config["ETHERSCAN_API_KEY"]
CONTRACT_ADDRESS = config["WETH_USDT_CONTRACT_ADDRESS"]
ETHERSCAN_BASE_URL = config["ETHERSCAN_BASE_URL"]
BINANCE_BASE_URL = config["BINANCE_BASE_URL"]


def test_get_block_timestamp():
    response = get_block_timestamp(ETHERSCAN_BASE_URL, ETHERSCAN_API_KEY, "0x10d4f")

    assert response is not None
    assert response == 1439296007

def test_get_first_block_after_timestamp():
    response = get_first_block_after_timestamp(ETHERSCAN_BASE_URL, ETHERSCAN_API_KEY, 1578638524)

    assert response is not None
    assert response == '9251483'