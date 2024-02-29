import requests

# Retrieve price of a given symbol at a given timestamp
def get_price(url, symbol, timestamp):
    # Binance API does not support timestamps before 2017-08-17
    if timestamp < 1502942460: return None

    # Convert timestamp to milliseconds
    timestamp_ms = int(timestamp * 1000)

    params = {
        "symbol": symbol,
        "interval": "1m",
        "startTime": timestamp_ms
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()

        if data:
            price = float(data[0][1])   # Open price
            return price

    return None

# Retrieve timestamp of a given block number
def get_block_timestamp(url, api_key, block_number):
    params = {
        "module": "proxy",
        "action": "eth_getBlockByNumber",
        "tag": block_number,
        "boolean": False,   # Individual transactions details
        "apikey": api_key
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        return int(response.json()["result"]["timestamp"], 16)
    else:
        return None

# Retrieve block number of the first block after a given timestamp
def get_first_block_after_timestamp(url, api_key, timestamp):
    params = {
        "module": "block",
        "action": "getblocknobytime",
        "timestamp": timestamp,
        "closest": "after",
        "apikey": api_key
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        return response.json()["result"]
    else:
        return None