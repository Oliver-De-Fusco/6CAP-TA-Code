
import numpy as np
import yfinance as yf
import seaborn as sns
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.dates as mdates
import matplotlib.ticker as mtick

import matplotlib.animation as animation
fig, ax1 = plt.subplots()

price, = ax1.plot([],[], label="Close")

def init():
    price.set_data([], [])
    return price,

# Animation update function
def update(frame):
    # Update data up to the current frame
    x = data_ichi.index[:frame]
    price.set_data(x, data_ichi['Close'].iloc[:frame])
    return price,
    

ani = animation.FuncAnimation(
    fig,
    update,
    frames=len(data_ichi),  # Number of frames (matches DataFrame length)
    init_func=init,
    blit=True,        # Optimize for static backgrounds
    interval=20       # Delay between frames in milliseconds
)

ani.save("animation/ichimoku.gif",writer="pillow",fps=30)
