import datetime


def to_unix(dt: datetime.datetime) -> int:
    return int(dt.timestamp() * 1000)


def to_isodate(dt: str) -> str:
    dt = int(dt) / 1000
    dt = datetime.datetime.utcfromtimestamp(int(dt))
    return dt.isoformat()