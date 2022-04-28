import os
from src.processor.monitor import Monitor

if __name__ == "__main__":

    runner = Monitor(api_key=os.getenv("API_KEY"),
                    secret=os.getenv("API_SECRET"),
                    password=os.getenv("API_PASS"),
                    db_uri=os.getenv("DB_URI"),
                    db_port=int(os.getenv("DB_PORT")),
                    where_from=(os.getenv("DB_NAME"), os.getenv("OHLC_COLLECTION_NAME")),
                    where_to=(os.getenv("DB_NAME"), os.getenv("TRADE_COLLECTION_NAME")),
                    pairs=os.getenv("PAIRS").split(';'))
    runner.run()
