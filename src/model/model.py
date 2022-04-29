import torch
import numpy as np
from src.utils.dts import *
import datetime
from src.model.model_core import DQN2d
from src.processor.ti_producer import TiGenerator
from src.api.mongo_api import MongoInterface as M


class Model:
    """
    Handles predictions and prediction update
    """
    def __init__(self, monitoring_list: list):

        self.model = DQN2d(150, 3)
        self.monitoring_list = monitoring_list

    def predict(self, array: np.ndarray) -> int:
        tensor = torch.Tensor(array)
        with torch.no_grad():
            prediction = self.model(tensor)
        return prediction.item()

    def monitor(self, TiG:TiGenerator, mongo_interface:M.MongoInterface):
        updated_list = dict()
        later_time = to_unix(datetime.datetime.now())
        for pair in self.monitoring_list:
            ti = TiG.goto_db_and_make_obs(inst_id=pair, later_time=later_time, mongo_int=mongo_interface)
            action = self.predict(ti.to_numpy())
            updated_list[pair] = action
        return updated_list
