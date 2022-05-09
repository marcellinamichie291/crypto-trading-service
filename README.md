# crypto-trading-service


1) Docker pipeline
   1) Use Dockerfile_for_base_image to create basic python image with all required dependencies
   2) On top of the image built in step 1 create image with executable code with Dockerfile
   3) Finally, run docker-compose.yml to create pod 
<br />
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