import time
import ccxt
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
