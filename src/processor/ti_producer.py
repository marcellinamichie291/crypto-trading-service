import pandas as pd
import numpy as np
import ta
import polars as pl

from scipy.signal.signaltools import wiener

from api import mongo_api as M
from exceptions import *


def standardize(ser):
    ser = ser.replace([np.inf, -np.inf], 0)
    return (ser - ser.mean()) / ser.std()


def smooth(ser):
    return pd.Series(wiener(ser.replace({np.nan: 0})), index=ser.index)


class TiGenerator:
    template = {
        "rsi_window": 0,
        "ppo_slow": 0,
        "ppo_fast_mult": 1,
        "ppo_signal_mult": 1,
        "roc_window": 0,
        "force_window": 0,
        "bb_pband_window": 0,
        "bb_pband_std": 1,
        "bb_kc_window": 0,
        "bb_kc_atr_mult": 1,
        "cci_window": 0,
        "cci_constant": 0.0,
    }

    def __init__(self):
        self.template["rsi_window"] = 20
        self.template["ppo_slow"] = 40
        self.template["ppo_fast_mult"] = 2
        self.template["ppo_signal_mult"] = 4
        self.template["roc_window"] = 10
        self.template["force_window"] = 20
        self.template["bb_pband_window"] = 10
        self.template["bb_pband_std"] = 2
        self.template["bb_kc_window"] = 20
        self.template["bb_kc_atr_mult"] = 2
        self.template["cci_window"] = 50
        self.template["cci_constant"] = 0.015

    def update_weights(self, **c):
        for key in c:
            if key not in self.template.keys():
                raise KeyError(f"No such parameter {key}")
            self.template[key] = c[key]

    def reset_weights(self):
        self.template["rsi_window"] = 20
        self.template["ppo_slow"] = 40
        self.template["ppo_fast_mult"] = 2
        self.template["ppo_signal_mult"] = 4
        self.template["roc_window"] = 10
        self.template["force_window"] = 20
        self.template["bb_pband_window"] = 10
        self.template["bb_pband_std"] = 2
        self.template["bb_kc_window"] = 20
        self.template["bb_kc_atr_mult"] = 2
        self.template["cci_window"] = 50
        self.template["cci_constant"] = 0.015

    def random_weights(self):
        self.template["rsi_window"] = np.random.randint(2, 51)
        self.template["ppo_slow"] = np.random.randint(2, 51)
        self.template["ppo_fast_mult"] = np.random.randint(1, 6)
        self.template["ppo_signal_mult"] = np.random.randint(1, 6)
        self.template["roc_window"] = np.random.randint(2, 51)
        self.template["force_window"] = np.random.randint(2, 51)
        self.template["bb_pband_window"] = np.random.randint(2, 51)
        self.template["bb_pband_std"] = np.random.randint(2, 5)
        self.template["bb_kc_window"] = np.random.randint(2, 51)
        self.template["bb_kc_atr_mult"] = np.random.randint(1, 6)
        self.template["cci_window"] = np.random.randint(2, 51)
        self.template["cci_constant"] = round(np.random.random(), 4)

    def get_ti(self, q: pl.DataFrame, tensor_length):

        coefs = self.template
        close = pd.Series(q["c"].to_numpy())
        high = pd.Series(q["h"].to_numpy())
        vol = pd.Series(q["vol_count"].to_numpy())
        low = pd.Series(q["l"].to_numpy())

        rsi = (
                ta.momentum.RSIIndicator(
                    close, window=coefs["rsi_window"], fillna=True
                ).rsi()
                / 100
        )
        ppo = ta.momentum.ppo_signal(
            close,
            window_slow=coefs["ppo_slow"],
            window_fast=int(coefs["ppo_slow"] / coefs["ppo_fast_mult"]),
            window_sign=int(
                (coefs["ppo_slow"] / coefs["ppo_fast_mult"]) / coefs["ppo_signal_mult"]
            ),
            fillna=True,
        )

        roc = ta.momentum.roc(close, window=coefs["roc_window"], fillna=True)

        force = ta.volume.force_index(
            close, vol, window=coefs["force_window"], fillna=True
        )
        adi = ta.volume.AccDistIndexIndicator(
            high, low, close, vol, fillna=True
        ).acc_dist_index()  # .pct_change()
        vpt = ta.volume.VolumePriceTrendIndicator(
            close, vol, fillna=True
        ).volume_price_trend()  # .pct_change()

        bb_pband = ta.volatility.BollingerBands(
            close,
            window=coefs["bb_pband_window"],
            window_dev=coefs["bb_pband_std"],
            fillna=True,
        ).bollinger_pband()
        bb_kc = ta.volatility.KeltnerChannel(
            high,
            low,
            close,
            window=coefs["bb_kc_window"],
            window_atr=int(coefs["bb_kc_window"] / coefs["bb_kc_atr_mult"]),
            fillna=True,
        ).keltner_channel_pband()

        # Trend
        cci = ta.trend.CCIIndicator(
            high,
            low,
            close,
            window=coefs["cci_window"],
            constant=coefs["cci_constant"],
            fillna=True,
        ).cci()
        # adx = ta.trend.adx_neg(q["<HIGH>"], q["<LOW>"], q["<CLOSE>"], window=30, fillna=True)

        new_q = pl.DataFrame(
            {
                "mm_rsi": smooth(rsi),
                "mm_ppo": smooth(standardize(ppo)),
                "mm_roc": smooth(standardize(roc)),
                "vl_adi": smooth(standardize(adi)),
                "vl_vpt": smooth(standardize(vpt)),
                "vl_force": smooth(standardize(force)),
                "vo_pband": smooth(standardize(bb_pband)),
                "bb_kc": smooth(standardize(bb_kc)),
                "tr_cci": smooth(standardize(cci)),
                # "tr_adx" : smooth(standartize(adx)))
            }
        )
        try:
            assert len(new_q) - tensor_length >= 0
        except AssertionError:
            raise NotEnoughData(f"Expected 300 obs, got {len(new_q)}")

        return new_q[len(new_q) - tensor_length:]

    def get_normalized_series(self, q: pl.DataFrame, tensor_length):

        q = q[len(q) - tensor_length:]
        qnew = q.with_columns(
            [
                (q['o'] / q['o'].tail(1)[0]).alias('o'),
                (q['h'] / q['h'].tail(1)[0]).alias('h'),
                (q['l'] / q['l'].tail(1)[0]).alias('l'),
                (q['c'] / q['c'].tail(1)[0]).alias('c'),
                (q['vol_count'] / q['vol_count'].max()).alias('vol_count')
            ]
        )
        return qnew[['o', 'h', 'l', 'c', 'vol_count']]

    def get_obs(self, q: pl.DataFrame, tensor_length):
        a = self.get_ti(q=q, tensor_length=tensor_length)
        b = self.get_normalized_series(q=q, tensor_length=tensor_length)
        return pl.concat([a, b], how='horizontal')

    def goto_db_and_make_obs(self, inst_id: str, later_time: int, mongo_int: M.MongoInterface):
        raw = pl.DataFrame(mongo_int.get_latest_batch(inst_id, later_time))
        
        if len(raw) == 0:
            raise ZeroObsException('Empty DB for a given ticker')

        raw = raw[['dt', 'o','h', 'l', 'c', 'vol_count', 'vol_coin']].sort(by=[pl.col('dt'), pl.col('vol_count')])
        raw = raw.with_column(pl.col('dt').shift(-1).alias('next_dt'))
        raw = raw.with_column(pl.when(pl.col('dt') != pl.col('next_dt')).then(1).otherwise(None).alias('candle_end'))
        raw = raw.drop_nulls()[['dt', 'o','h', 'l', 'c', 'vol_count', 'vol_coin']]

        if len(raw) < 300:
            raise NotEnoughData(f"Expected 300 obs, got {len(raw)}")

        return self.get_obs(raw, 150)