
# Application
### Build and Run code
1. Pull repository and change directory to root folder

2. Add your Etherscan API in `config.sample.json`. Rename file to `config.json`

3. Install Docker and run from CLI:  
`docker-compose up --build`

This will bring up the server on `localhost:8000`.  
It will automatically reroute to Swagger docs, where the endpoints can be tested.

Transactions (live and historical) are processed and stored in `transactions.db`.

### Tests
1. Copy the `config.json` file into `tests/` directory.
2. Install pytest  
`pip install pytest==7.1.3`
3. From root directory, execute: `pytest`.  
This will execute 8 unit tests.

Note: There is a unit test `test_transaction_not_in_db` in `test_main.py`. Replace the `transaction_hash` parameter with a new (random) hash.

# Notes
1. Application always attempts to read transactions from database before querying the API (in order to minimize total API calls).
2. Each time transaction(s) is/are queried, application writes it to db as well. 
3. Live transactions are recorded after every 40 seconds.   
In case of API exception/failure, reattempt after 40 seconds.
4. To convert ETH to USDT, I used __open price__ from Binance `klines` API.


__Improvements I would have liked to make:__
- Rate Limiter for APIs
- Make application and DB asynchronous (especially useful in case of historical batch processing)
- Handle exceptions from API more thoroughly
- Better project structure / code organization.
