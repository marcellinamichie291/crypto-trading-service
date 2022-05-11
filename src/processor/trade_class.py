from dataclasses import dataclass
from dataclasses import asdict
from dataclasses import field


@dataclass
class Trade:
    instId: str
    side: str

    open_ts:int
    open_amount_quote: float
    open_amount_base: float
    open_price_base: float
    open_id: str

    close_ts: int = None
    close_amount_quote: float = None
    close_amount_base: float = None
    close_price_base: float = None
    close_id: str = None

    time_alive: float = None
    is_open: bool = True
    is_positive: bool = None
    relative_return: float = None
    absolute_return: float = None
    fees_in_base: list = field(default_factory=list)

    def _absolute_return(self) -> None:
      if self.close_price_base is not None:
        self.absolute_return = ((self.close_amount_base
                                 -sum(self.fees_in_base))
                                 /self.open_amount_base)-1

    def _relative_return(self) -> None:
      if self.close_price_base is not None:
        coef = 1 if self.side == 'buy' else -1
        self.relative_return = (((self.close_amount_base
                                 -sum(self.fees_in_base))
                                 /self.open_amount_base)-1) * coef

        self.is_positive = True if self.relative_return >0 else False

    def _time_alive(self) -> None:
      if self.close_ts is not None:
        self.time_alive = self.close_ts - self.open_ts

    def dict(self):
      return asdict(self)

    def close(self, close_ts=None, close_price=None) -> dict:

        if close_ts is not None:
            self.close_ts = close_ts
        if close_price is not None:
            self.close_price_base = close_price

        self._absolute_return()
        self._relative_return()
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
        trd.fees_in_base.append(r['fee']['cost'])
        return trd

    def modify_on_close(self, r:dict):
        self.close_ts = r['timestamp']
        self.close_amount_quote = r['cost']
        self.close_amount_base = r['amount']
        self.close_price_base = r['average']
        self.close_id = r['id']
        return self
