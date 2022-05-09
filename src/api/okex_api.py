import os
import time
import math
import requests
import datetime
import ccxt
from utils import dts
from ccxt.base.errors import BadSymbol


class Market:
    def __init__(self, api_key: str, secret: str, password: str, verbose=False, is_sandbox=True):

        self.m = ccxt.okx({
            'apiKey': api_key,
            'secret': secret,
            'password': password,
            'verbose': verbose
        })
        if is_sandbox:
            self.m.set_sandbox_mode(enable=True)

    def create_order(self, symbol, type, side, amount, params={}):
        r = self.m.create_order(symbol=symbol, type=type, side=side, amount=amount, params=params)
        time.sleep(0.5)
        info = self.get_trade_info(symbol=symbol, id=r['id'])
        return info

    def get_trade_info(self, symbol, id):
        return self.m.fetch_order(id=id, symbol=symbol)

    def fetch_balance_usd(self):
        raw_b = self.m.fetch_balance()
        d = {}
        for elem in raw_b['info']['data'][0]['details']:
            d[elem['ccy']] = float(elem['eqUsd'])
        return d

    def reset_balance(self):
        valid_pairs = ['ADA', 'AVAX', 'DOGE', 'DOT', 'ETH', 'LUNA', 'SOL', 'USDT', 'XRP']
        active_balances = self.m.fetch_balance()
        for position in active_balances['info']['data'][0]['details']:
            if position['ccy'] not in valid_pairs:
                try:
                    self.create_order(f"{position['ccy']}-USDT", type="market", side="sell",
                                      amount=position['availBal'], params={"tgtCcy": "base_ccy"})
                    time.sleep(5)
                except BadSymbol:
                    pass
                    time.sleep(2)

    @staticmethod
    def get_candles(pair: str, older_time: datetime.datetime):
        insertable_documents = []
        step_msec = 60000
        per_page = 100
        URL_BASE = "https://www.okex.com"
        HEADERS = {
            "OK-ACCESS-KEY": os.getenv('API_KEY'),
            "OK-ACCESS-SIGN": os.getenv('API_SECRET'),
        }

        now = dts.to_unix(datetime.datetime.now())
        body = {
            "instId": pair,
            "after": str(now),
        }
        keys = {
               0: "dt",
               1: "o",
               2: "h",
               3: "l",
               4: "c",
               5: "vol_count",
               6: "vol_coin"}

        loops = math.ceil(((now - dts.to_unix(older_time)) / step_msec) / per_page)
        for step in range(loops):
            a = requests.get(
                URL_BASE + "/api/v5/market/history-candles", headers=HEADERS, params=body
            )

            if len(a.json()["data"]) == 0:
                now -= step * step_msec * per_page
            else:
                now = a.json()["data"][-1][0]  # Time of the last candle in this batch

            for cndl in a.json()["data"]:
                d_ = {keys[k]: float(cndl[k]) for k in keys}
                d_['instId'] = pair
                insertable_documents.append(d_)

            body = {
                "instId": pair,
                "after": str(now),
            }
            time.sleep(0.05)
        return insertable_documents
