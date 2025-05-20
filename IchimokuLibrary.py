import pandas as pd
import numpy as np

# Exits


def ex_l_1(data):
    return data["Close"] < data["kijin"]


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
    return data["Close"] > data["kijin"]


def ex_s_2(data):
    return l_2(data) & (data["Close"] > data["kijin"])


def ex_s_3(data):
    return l_1(data) & l_2(data) & (data["Close"] > data["kijin"])


def ex_s_4(data):
    return l_1(data) & l_2(data) & l_3(data) & (data["Close"] > data["kijin"])


def ex_s_5(data):
    return s_1(data) & (data["Close"] < data["kijin"])


# Entries

def en_l_1(data):
    return l_1(data) & (data["Close"] > data["kijin"])


def en_l_2(data):
    return l_2(data) & (data["Close"] > data["kijin"])


def en_l_12(data):
    return l_1(data) & l_2(data) & (data["Close"] > data["kijin"])


def en_l_123(data):
    return l_1(data) & l_2(data) & l_3(data) & (data["Close"] > data["kijin"])


def en_s_1(data):
    return s_1(data) & (data["Close"] < data["kijin"])


def en_s_2(data):
    return s_2(data) & (data["Close"] < data["kijin"])


def en_s_12(data):
    return s_1(data) & s_2(data) & (data["Close"] < data["kijin"])


def en_s_123(data):
    return s_1(data) & s_2(data) & s_3(data) & (data["Close"] < data["kijin"])

# Entry Bullish patterns


def l_1(data):
    return data["tenkan"] > data["kijin"]


def l_2(data):
    return data["chikou"] > data["Close"]


def l_3(data):
    # Check span a and span b offsets
    return data["Close"] > np.max([data["span_a"], data["span_b"]], axis=0)

# Exit Bearish patterns


def s_1(data):
    return data["tenkan"] < data["kijin"]


def s_2(data):
    return data["chikou"] < data["Close"]


def s_3(data):
    # Check span a and span b offsets
    return data["Close"] < np.min([data["span_a"], data["span_b"]], axis=0)


# CONSTANTS
# Strategy Registries (define these at module level)
EXIT_REGISTRY = {
    'ex_l_1': ex_l_1,  # Replace with actual function references
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


def kijin(data, t=26):
    return (((data.rolling(t).max()) + (data.rolling(t).min())) / 2).rename("kijin")


def chikou(data, t=26):
    return (data.shift(-t)).rename("chikou")


def span_a(data, t_short=9, t_mid=26):
    return ((((tenkan(data, t_short) + kijin(data, t_mid))) / 2).shift(t_mid)).rename("span_a")


def span_b(data, t_mid=26, t_long=52):
    return ((((data.rolling(t_long).max()) + (data.rolling(t_long).min())) / 2).shift(t_mid)).rename("span_b")


def apply_ichi(data, short=9, medium=26, long=52):
    """
    data : pandas.core.series.Series

    returns : pandas.core.frame.DataFrame
    """
    if not isinstance(data, pd.Series):
        raise TypeError(f"input data must be {pd.Series}")

    data = data.copy()

    _tenkan = tenkan(data, short)
    _kijin = kijin(data, medium)
    _chikou = chikou(data, medium)
    _span_a = span_a(data, short, medium)
    _span_b = span_b(data, medium, long)

    return pd.concat([data, _tenkan, _kijin, _chikou, _span_a, _span_b], axis=1)


def trade(data, entry, exit, short=9, medium=26, long=52):
    """
    data = log returns of closing prices using pandas series.
    entry and exit are functions. 
    """

    ichi_data = apply_ichi(data, short, medium, long)

    # Jank af
    if isinstance(entry, str):
        entry = ENTRY_REGISTRY[entry]
    if isinstance(exit, str):
        exit = EXIT_REGISTRY[exit]

    # Apply entry and exit signals
    mask_1 = (entry(ichi_data).dropna() == 1) & (
        entry(ichi_data).dropna().shift(1) == 0)
    mask_2 = (exit(ichi_data).dropna() == 1) & (
        exit(ichi_data).dropna().shift(1) == 0)

    df = pd.concat([mask_1, mask_2, pd.Series(
        np.zeros(mask_1.shape), index=mask_1.index)], axis=1)
    df.columns = ["col1", "col2", "col3"]

    buy_state = 0
    col3_values = []

    # Iterate
    for index, row in df.iterrows():
        col3_values.append(buy_state)
        if row['col1']:
            buy_state = 1
        elif row['col2']:
            buy_state = 0

    df['col3'] = col3_values
    performance = (data * df["col3"])

    return performance


def sharpe_ratio(data, entry, exit, short=9, medium=26, long=52):
    x = trade(data, entry, exit, short, medium, long)
    mu, sigma = 12 * x.mean(), np.sqrt(12 * x.var())
    values = np.array([mu, sigma, mu / sigma]).squeeze()
    index = ["mu", "sigma", "Sharpe"]
    return pd.Series(values, index=index)
