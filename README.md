# crypto-trading-service


Required env variables

* LOGGER_PATH - path to log file
* API_KEY - OKX key
* API_SECRET - OKX secret
* API_PASS - OKX passphrase
* DB_URI - uri to mongo instance
* DB_PORT - port for uri 
* DB_NAME - name of db where data will be stored
* OHLC_COLLECTION_NAME - name of the collection for stroing OHLC data
* TRADE_COLLECTION_NAME - name of the collection for storing closed trades
* PAIRS - semi-colon separated paris used for trading
* MODEL_PATH - path to pretrained model
