# crypto-trading-service


1) Docker pipeline
   1) Use Dockerfile_for_base_image to create basic python image with all required dependencies but no code.
   2) Use Dokerfile to create python image with code only.
   3) Finally, run docker-compose.yml to create pod, which runs cont. with image 1 and cont. with image 2 simultaneously.

2) Required env variables

      * LOGGER_PATH - path to log file
      * API_KEY - OKX key
      * API_SECRET - OKX secret
      * API_PASS - OKX passphrase
      * DB_URI - uri to mongo instance
      * DB_PORT - port for uri 
      * DB_NAME - name of db where data will be stored
      * OHLC_COLLECTION_NAME - name of the collection for stroing OHLC data
      * TRADE_COLLECTION_NAME - name of the collection for storing closed trades
      * PAIRS - semicolon-separated paris used for trading
      * MODEL_PATH - path to pretrained model
