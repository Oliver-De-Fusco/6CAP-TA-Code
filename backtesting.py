from dataclasses import dataclass, field
from datetime import datetime
from math import log
import pandas as pd
import warnings

@dataclass
class Trade:
    asset: str
    is_long: bool
    quantity: int
    date: datetime
    price: float

    @property
    def value(self):
        return self.price * self.quantity


class Strategy:
    def __init__(self, logic,security=None):
        self.security = security
        self.logic = logic
        
        def trade(self, data):
            is_long = None
            quantity = None

            quantity, is_long = self.logic(data)

            return Trade(self.security,is_long,quantity,data.index[-1],data['close'][-1])


class Backtest:

    def __init__(self, strategy, data,cash=100_000):
        self.start_cash = cash
        self.cash = cash
        self.trade_history = pd.DataFrame(columns=Trade.__dict__.keys())
        
        if isinstance(strategy,Strategy):
            self.strategy = strategy
        else:
            raise ValueError
        
        if isinstance(data,pd.DataFrame):
            self.data = data
        else:
            raise ValueError
    
    def trade(self, trade):
        if trade.is_long:
            if self.cash < trade.value:
                raise ValueError("Low balance")
            else:
                self.cash -= trade.value

        else:
            self.cash += trade.value
        
        self.trade_history.iloc[len(self.trade_history)+1] = trade.__dict__


    def backtest(self):

        for x in range(len(self.data)):
            window = self.data[:x]

            trade = self.strategy.trade(window)
            
            try:
                self.trade(trade)
            except ValueError:
                warnings.warn(f"Out of cash at : {window.index[x]}")
                break
    
    def calculate_pnl(self):
        pass


