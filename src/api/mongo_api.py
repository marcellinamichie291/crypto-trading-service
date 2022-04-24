import typing
from pymongo import MongoClient


class MongoInterface:

    def __init__(self,
                 uri: str,
                 port: int,
                 where_from: typing.Tuple[str, str],
                 where_to: typing.Tuple[str, str]) -> None:
        """
        :param uri: mongo connection string
        :param port:
        :param where_from: source tuple(db_name, collection_name)
        :param where_to: save tuple(db_name, collection_name)
        """
        self.client = MongoClient(uri, port)
        self.coll_from = self.client[where_from[0]][where_from[1]]
        self.coll_to = self.client[where_to[0]][where_to[1]]
        self.all_keys = ['_id', 'instId', 'dt', 'o', 'h', 'l', 'c', 'vol_count', 'vol_coin']

    def get_latest_batch(self, inst_id: str, later_time: int) -> dict:
        _ = self.coll_from.find(
            {
                "instId": inst_id,
                "dt": {"$lt": later_time}
            }
        ).sort("dt", -1)[:10_000]
        _ = [x for x in _]
        return {k: [d[k] for d in _ if k in d] for k in self.all_keys}

