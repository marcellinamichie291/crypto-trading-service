from dataclasses import dataclass
from dataclasses import asdict
from dataclasses import field


@dataclass
class Trade:
    instId: str
    side: str

    open_ts:int
    open_amount_quote: float  # gross of fees
    open_amount_base: float  # gross of fees
    open_price_base: float
    open_id: str

    close_ts: int = None
    close_amount_quote: float = None  # net of first fee / gross of second fee
    close_amount_base: float = None  # net of first fee / gross of second fee
    close_price_base: float = None
    close_id: str = None

    time_alive: float = None
    is_open: bool = True
    is_positive: bool = None

    rel_ret_base: float = None
    rel_ret_quote: float = None
    abs_ret_base: float = None
    abs_ret_quote: float = None
    net_price_ret_base: float = None
    net_price_ret_quote: float = None

    fees_in_base: list = field(default_factory=list)
    fees_in_quote: list = field(default_factory=list)

    def _calculate_returns(self) -> None:
        if self.close_price_base is not None:
            close_base_amnt_net = self.close_amount_base - self.fees_in_base[1]
            open_base_amnt_net = self.open_amount_base - self.fees_in_base[0]

            close_quote_amnt_net = self.close_amount_quote - self.fees_in_quote[1]
            open_quote_amnt_net = self.open_amount_quote - self.fees_in_quote[0]

            self.net_price_ret_base = (close_base_amnt_net/open_base_amnt_net)-1
            self.net_price_ret_quote = (close_quote_amnt_net/open_quote_amnt_net)-1

            self.abs_ret_base = (close_base_amnt_net / (open_base_amnt_net+sum(self.fees_in_base))) - 1
            self.abs_ret_quote = (close_quote_amnt_net / (open_quote_amnt_net+sum(self.fees_in_quote))) - 1

            coef = 1 if self.side == 'buy' else -1

            self.rel_ret_base = self.abs_ret_base * coef
            self.rel_ret_quote = self.abs_ret_quote * coef

            self.is_positive = True if self.rel_ret_quote > 0 else False

    def _time_alive(self) -> None:
        if self.close_ts is not None:
            self.time_alive = self.close_ts - self.open_ts

    @staticmethod
    def _calculate_fees(r):
        if r['fee']['currency'] == 'USDT':
            fees_in_usdt = r['fee']['cost']
            fees_in_base = r['fee']['cost'] * (1/r['average'])
        else:
            fees_in_usdt = r['fee']['cost'] * r['average']
            fees_in_base = r['fee']['cost']

        return fees_in_base, fees_in_usdt

    def dict(self):
        return asdict(self)

    def close(self, close_ts=None, close_price=None) -> dict:

        if close_ts is not None:
            self.close_ts = close_ts
        if close_price is not None:
            self.close_price_base = close_price

        self._calculate_returns()
        self._time_alive()

        self.is_open = False

        return self.dict()

    @classmethod
    def create_from_response(cls, r: dict):
        trd = cls(
          instId = r['info']['instId'],
          side = r['info']['side'],
          open_ts = int(r['timestamp']),
          open_amount_quote = float(r['cost']),
          open_amount_base = float(r['amount']),
          open_price_base = float(r['average']),
          open_id = r['id'])

        fees_in_base, fees_in_usdt = cls._calculate_fees(r)
        trd.fees_in_base.append(fees_in_base)
        trd.fees_in_quote.append(fees_in_usdt)

        return trd

    def modify_on_close(self, r: dict):
        self.close_ts = r['timestamp']
        self.close_amount_quote = r['cost']
        self.close_amount_base = r['amount']
        self.close_price_base = r['average']
        self.close_id = r['id']

        fees_in_base, fees_in_usdt = self._calculate_fees(r)
        self.fees_in_base.append(fees_in_base)
        self.fees_in_quote.append(fees_in_usdt)

        return self

