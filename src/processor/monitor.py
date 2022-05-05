import time
from utils.logger import log
from api.mongo_api import MongoInterface
from api.okex_api import Market
from processor.trade_class import Trade
from model.model_instance import Model
from utils.dts import *
from processor.ti_producer import TiGenerator


class Monitor:

    def __init__(self, api_key: str,
                 secret: str,
                 password: str,
                 db_uri: str,
                 db_port: int,
                 where_from: tuple,
                 where_to: tuple,
                 pairs: list):

        self.exchange = Market(api_key, secret, password)
        self.mongo = MongoInterface(db_uri, db_port, where_from, where_to)
        self.model = Model(monitoring_list=pairs)
        self.tiger = TiGenerator()

        self.positions = {'long': set(), 'short': set()}
        self.cache = []

        self.cooldown_period = 180000  # msec
        self.max_hold_period = 270000  # msec
        self.max_load = 1500
        self.basic_bid = 1000

    def get_from_cache(self, pair):
        all = []
        for elem in self.cache:
            if elem.instId == pair:
                all.append(elem)
        return all

    def delete_from_cache(self, pair):
        this_one = None
        for elem in self.cache:
            if elem.instId == pair:
                this_one = elem
        self.cache.remove(this_one)
        return

    def batch_close(self, trades: list):
        to_delete = []
        for trade in trades:
            t = self.create_reverse_order(T=trade)
            self.mongo.post_one(t.dict())
            to_delete.append(trade)
        for t in to_delete:
            self.cache.remove(t)

    def action_resolution(self, action: int, pair: str):
        """Function resolves trades in context of actions predicted by the model"""

        if action == 1:
            return

        # New
        if action == 0 and (pair not in self.positions['short'] and part not in self.positions['long']):
            log.info(f'Short signal for {pair} - skipping (no short)')
            return

        elif action == 2 and (pair not in self.positions['long'] and pair not in self.postions['short']):
            r = self.m.create_order(symbol=pair,
                                    type='market',
                                    side='buy',
                                    amount=1000,
                                    params={'tgtCcy': 'quote_ccy'})
            trd = Trade.create_from_response(r)
            self.cache.append(trd)
            self.positions['long'].add(pair)
            log.info(f'Long signal for {pair} - opening (amnt$: 1000)')
            return

        # Amend
        elif action == 0 and pair in self.positions['short']:
            # Impossible case for now
            return
        elif action == 0 and pair in self.positions['long']:
            trades = self.get_from_cache(pair)
            self.batch_close(trades)
            for trade in trades:
                log.info(f'Short signal for {pair} - closing reversed (amnt$: {trade.close_amount_quote})')
            return

        elif action == 2 and pair in self.positions['short']:
            # Impossible case for now
            return

        elif action == 2 and pair in self.positions['long']:
            balances = self.exchange.fetch_balance_usd()
            amount = balances[pair.split("-")[0]]
            if amount >= self.max_load:
                log.info(f'Short signal for {pair} - skipping (max amount exceeded)')
                return
            else:
                # check cooldown
                trades = self.get_from_cache(pair)
                for trade in trades:
                    if trade.open_ts + self.cooldown_period > to_unix(datetime.datetime.now()):
                        log.info(f'Long signal for {pair} - skipping (cooldown period)')
                        return

                # Increase position
                diff = self.max_load - amount
                assert diff > 0
                r = self.m.create_order(symbol=pair,
                                        type='market',
                                        side='buy',
                                        amount=diff,
                                        params={'tgtCcy': 'quote_ccy'})
                trd = Trade.create_from_response(r)
                self.cache.append(trd)
                self.positions['long'].add(pair)
                log.info(f'Long signal for {pair} - opening (amnt$: {diff})')
                return

    def create_reverse_order(self, T: Trade) -> Trade:
        sd = "buy" if T.side == 'sell' else "sell"
        r = self.exchange.create_order(symbol=T.instId,
                                       type='market',
                                       side=sd,
                                       amount=T.open_amount_base,
                                       params={"tgtCcy": "base_ccy"})
        return T.modify_on_close(r)

    def process_cache(self):
        to_delete = []
        if len(self.cache) == 0:
            return
        for trade in self.cache:
            if trade.open_ts + self.max_hold_period > to_unix(datetime.datetime.now()):
                to_delete.append(trade)
        self.batch_close(to_delete)
        for t in to_delete:
            side = "Long" if t.side == "buy" else "Short"
            log.info(f'{side} trade for {t.instId} was closed. Max holding period excceded.')

    def run(self):

        while True:
            try:
                self.process_cache()
                actions = self.model.monitor(self.tiger, self.mongo)
                for k in actions:
                    self.action_resolution(actions[k], k)
                time.sleep(10)
                
            except (NotEnoughData, ZeroObsException):
                log.warning("Not enough data collected. Hibernating for 10 minutes.")
                time.sleep(600)
                
            except Exception as e:
                log.exception(e)


