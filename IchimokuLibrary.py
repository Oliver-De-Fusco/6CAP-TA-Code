import pandas as pd
import numpy as np
import arch.bootstrap as ab
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Exits


def ex_l_1(data):
    return data["Close"] < data["kijun"]


def ex_l_2(data):
    # TK(t) < KJ(t)
    return s_1(data)


def ex_l_3(data):
    # CK(t) < P_L(t-25)
    return s_2(data)


def ex_l_4(data):
    # TK(t) < KJ(t) & (CK(t) < P L(t − 25))
    return s_1(data) & s_2(data)


def ex_l_5(data):
    # (TK(t) < KJ(t)) & (CK(t) < P L(t − 25)) & P c(t) < min{SKA(t − 25), SKB(t − 25)}
    return s_1(data) & s_2(data) & s_3(data)


# !!! WIP !!!
def ex_s_1(data):
    return data["Close"] > data["kijun"]


def ex_s_2(data):
    return l_2(data) & (data["Close"] > data["kijun"])


def ex_s_3(data):
    return l_1(data) & l_2(data) & (data["Close"] > data["kijun"])


def ex_s_4(data):
    return l_1(data) & l_2(data) & l_3(data) & (data["Close"] > data["kijun"])


def ex_s_5(data):
    return s_1(data) & (data["Close"] < data["kijun"])


# Entries

def en_l_1(data):
    return l_1(data) & (data["Close"] > data["kijun"])


def en_l_2(data):
    return l_2(data) & (data["Close"] > data["kijun"])


def en_l_12(data):
    return l_1(data) & l_2(data) & (data["Close"] > data["kijun"])


def en_l_123(data):
    return l_1(data) & l_2(data) & l_3(data) & (data["Close"] > data["kijun"])


def en_s_1(data):
    return s_1(data) & (data["Close"] < data["kijun"])


def en_s_2(data):
    return s_2(data) & (data["Close"] < data["kijun"])


def en_s_12(data):
    return s_1(data) & s_2(data) & (data["Close"] < data["kijun"])


def en_s_123(data):
    return s_1(data) & s_2(data) & s_3(data) & (data["Close"] < data["kijun"])

# Entry Bullish patterns


def l_1(data):
    return data["tenkan"] > data["kijun"]


def l_2(data):
    return  data["Close"] > data["chikou"]

def l_3(data):
    # Check span a and span b offsets
    return data["Close"] > np.max(data[["span_a","span_b"]],axis=1)

# Exit Bearish patterns


def s_1(data):
    return data["tenkan"] < data["kijun"]


def s_2(data):
    return data["Close"] < data["chikou"]


def s_3(data):
    # Check span a and span b offsets
    return data["Close"] < np.min(data[["span_a","span_b"]], axis=1)


# CONSTANTS
# Strategy Registries (define these at module level)
EXIT_REGISTRY = {
    'ex_l_1': ex_l_1,
    'ex_l_2': ex_l_2,
    'ex_l_3': ex_l_3,
    'ex_l_4': ex_l_4,
    'ex_l_5': ex_l_5
}

ENTRY_REGISTRY = {
    'en_l_1': en_l_1,
    'en_l_2': en_l_2,
    'en_l_12': en_l_12,
    'en_l_123': en_l_123
}

# Refactored parameter space using string keys
STRATEGIES_L = [
    ['ex_l_1', ['en_l_1', 'en_l_2', 'en_l_12', 'en_l_123']],
    ['ex_l_2', ['en_l_1', 'en_l_12', 'en_l_123']],
    ['ex_l_3', ['en_l_2', 'en_l_12', 'en_l_123']],
    ['ex_l_4', ['en_l_12', 'en_l_123']],
    ['ex_l_5', ['en_l_123']]
]

BULLISH_SIGNALS = [l_1, l_2, l_3]

BEARISH_SIGNALS = [s_1, s_2, s_3]

ENTRY_SIGNALS_BULL = [en_l_1, en_l_2, en_l_12, en_l_123]

ENTRY_SIGNALS_BEAR = [en_s_1, en_s_2, en_s_12, en_s_123]

# ICHIMOKU FUNCTIONS


def tenkan(data, t=9):
    return (((data.rolling(t).max()) + (data.rolling(t).min())) / 2).rename("tenkan")


def kijun(data, t=26):
    return (((data.rolling(t).max()) + (data.rolling(t).min())) / 2).rename("kijun")


def chikou(data, t=26):
    return (data.shift(-t)).rename("chikou")


def span_a(data, t_short=9, t_mid=26):
    return ((((tenkan(data, t_short) + kijun(data, t_mid))) / 2)).shift(-t_mid).rename("span_a")


def span_b(data, t_mid=26, t_long=52):
    return ((((data.rolling(t_long).max()) + (data.rolling(t_long).min())) / 2)).shift(-t_mid).rename("span_b")


def apply_ichi(data, short=9, medium=26, long=52):
    """
    data : pandas.core.series.Series

    returns : pandas.core.frame.DataFrame
    """
    if not isinstance(data, pd.Series):
        raise TypeError(f"input data must be {pd.Series}")

    data = data.copy()

    _tenkan = tenkan(data, short)
    _kijun = kijun(data, medium)
    _chikou = chikou(data, medium)
    _span_a = span_a(data, short, medium).shift(medium)
    _span_b = span_b(data, medium, long).shift(medium)

    return pd.concat([data, _tenkan, _kijun, _chikou, _span_a, _span_b], axis=1)


def trade(data, entry, exit, short, medium, long):
    # logger.info(f"trading {entry} - {exit}")
    """
    data = log returns of closing prices using pandas series.
    entry and exit are functions. 
    """

    ichi_data = apply_ichi(data.cumsum(), short, medium, long).dropna()

    # Jank af
    if isinstance(entry, str):
        entry = ENTRY_REGISTRY[entry]
    if isinstance(exit, str):
        exit = EXIT_REGISTRY[exit]


    entry_signal = entry(ichi_data)
    exit_signal = exit(ichi_data)

    mask_1 = (entry_signal == 1) & (entry_signal.shift(1) == 0)
    mask_2 = (exit_signal == 1) & (exit_signal.shift(1) == 0)

    # Use NumPy for state computation
    entry_np = mask_1.to_numpy()
    exit_np = mask_2.to_numpy()
    n = len(entry_np)
    state_np = np.zeros(n, dtype=bool)
    current_state = 0

    for i in range(n):
        state_np[i] = current_state
        if entry_np[i]:
            current_state = 1
        elif exit_np[i]:
            current_state = 0

    performance = data.iloc[-n:] * state_np  # Align with the last n values
    # Calculate and add costs
    # cost_value = np.log(1 - 0.005)
    # cost_vector = np.zeros(n)
    # cost_vector[entry_np] += cost_value
    # cost_vector[exit_np] += cost_value

    return performance


def sharpe_ratio(data, entry, exit, short, medium, long, days=252):
    x = trade(data, entry, exit, short, medium, long)
    mu, sigma = days * x.mean(), np.sqrt(days * x.var())

    values = np.array([mu, sigma, mu / sigma]).squeeze()
    index = ["mu", "sigma", "Sharpe"]
    return pd.Series(values, index=index)


def confidence_interval(bs, metric, short, medium, long, strategy, n=750, days=252):

        extra_kwargs = {"short":short, "medium":medium, "long":long, "exit":strategy[0], "entry":strategy[1], "days":days}

        # logger.info(f"Simulating {extra_kwargs["exit"]} - {extra_kwargs["entry"]}")
        out = bs.conf_int(metric, n, extra_kwargs=extra_kwargs)
        logger.debug(f"Completed simulation for {extra_kwargs}")
        
        return (extra_kwargs, out)