# Use binance api to establish websockets
# Use finplot to draw and update lines

# https://github.com/highfestiva/finplot

import colorsys
from os import path, remove
from datetime import datetime, timedelta

import finplot as fplt
import pandas as pd

from binance.client import Client
from binance.websockets import BinanceSocketManager
from binance.enums import *

from PyQt5.QtWidgets import QComboBox, QCheckBox, QWidget, QLineEdit, QRadioButton, QFormLayout, QLabel
from pyqtgraph import QtGui
import pyqtgraph as pg

#Max 1200 requests per minute; 10 orders per second; 100,000 orders per 24hrs
client = Client()
bm = BinanceSocketManager(client)

# Globals
symbol_list = []

# Use the symbol_list and store dictionaries in it
symbol_dict = dict.fromkeys(symbol_list, pd.DataFrame())

# 
sorted_volume = pd.DataFrame()

# fplt.plots created are stored here
plots = {}

# TradingView style
# https://github.com/highfestiva/finplot/wiki/Settings
fplt.foreground = '#7a7c85'
fplt.background = '#131722'
fplt.cross_hair_color = '#ffffff'
fplt.legend_fill_color   = '#000000'

# Sets list of top 25 coins on Binance, based on volume
# Is a bit slow
def top_volume():

    global sorted_volume

    # Check for recent pickle
    if (path.exists("sorted_volume.pkl")):

        print("Found pickle")

        # If it exist, unpickle and use that as sorted_volume
        mtime = path.getmtime("sorted_volume.pkl")
        last_modified_date = datetime.fromtimestamp(mtime)
        
        # Check if it is older than 24h
        old = datetime.now() - timedelta(days=1)

        # If last_modified_date is older than 24h
        if (last_modified_date < old):
            print("Old pickle")
            # Delete old pickle and call method again
            remove("sorted_volume.pkl")
            top_volume()
        else:
            print("Using recent pickle")

            df = pd.read_pickle("./sorted_volume.pkl")
            sorted_volume = df

    # Else, get recent volume
    else:

        # Includes all symbols on Binance
        symbols = client.get_exchange_info().get("symbols")

        # Convert to dataframe
        df = pd.DataFrame(symbols)

        # Only get those that contain USDT
        df = df[df.quoteAsset.str.contains("USDT")]
        df = df[df.status == 'TRADING']
        df = df[df.permissions.map(set(['SPOT']).issubset)]

        stableCoins = ["USDCUSDT", "BUSDUSDT", "TUSDUSDT", "PAXUSDT", "EURUSDT", "GBPUSDT"] 

        # Drop the stable coins
        df = df[~df['symbol'].isin(stableCoins)]

        print("Getting volume...")
        df['volume'] = df['symbol'].apply(lambda x: client.get_klines(symbol = x, interval='1d', limit=1)[0][7])

        # Change it to numerical
        df['volume'] = pd.to_numeric(df['volume'])

        # Drop everything else
        df = df.filter(['symbol', 'volume'])

        # Sort by volume, first row has lowest volume
        df = df.sort_values(by=['volume'], ascending=False)

        sorted_volume = df

        # Save as pickle
        sorted_volume.to_pickle("./sorted_volume.pkl")

        # Print, to know if done
        print("Sorted volume")

# Set symbol_list based on number in textbox
def change_assets():
    # Set it to global list
    global symbol_list
    global sorted_volume
    global symbol_dict

    number = ctrl_panel.amount.text()
    if number == '':
        number = 0
    else:
        number = int(number)

    symbol_list = list(sorted_volume.head(number)['symbol'])

    symbol_dict = dict.fromkeys(symbol_list, pd.DataFrame())

    timeframe = ctrl_panel.timeframe.currentText()

    # remove any previous plots
    ax.reset()

    make_plot(ax, timeframe)

    fplt.refresh()

# === Websocket interpreter ===
# info gets updated every second
def ws_response(info):
    """ Info consists of:
    'e': '24hrMiniTicker',  # Event type
    'E': 1515906156273,     # Event time
    's': 'QTUMETH',         # Symbol
    'c': '0.03836900',      # close
    'o': '0.03953500',      # open
    'h': '0.04400000',      # high
    'l': '0.03756000',      # low
    'v': '147435.80000000', # volume
    'q': '5903.84338533'    # quote volume
    """

    try:
        crypto_data = [d for d in info if d['s'] in symbol_list]

        for k in crypto_data:

            global symbol_dict

            sym = k['s']

            df = symbol_dict[sym]

            close = float(k['c'])

            # t is the timestamp in ms
            t = int(k['E'])

            # index[-2] sometimes out of bound
            t0 = int(df.index[-2].timestamp()) * 1000
            t1 = int(df.index[-1].timestamp()) * 1000
            t2 = t1 + (t1-t0)

            # Update line corresponding with symbol
            if t < t2:
                # update last candle
                i = df.index[-1]
                close = float(k['c'])
                df.loc[i, 'Close']  = close
                df.loc[i, 'Diff'] = (close - df['Close'][0]) / df['Close'][0] * 100
            else:
                # create a new candle
                close = float(k['c'])
                diff = (close - df['Close'][0]) / df['Close'][0] * 100

                # Add it all together
                data = [t] + [close] + [diff]
                candle = pd.DataFrame([data], columns='Time Close Diff'.split()).astype({'Time':'datetime64[ms]'})
                candle.set_index('Time', inplace=True)
                df = df.append(candle)

            symbol_dict[sym] = df

    # Catch any exception
    except Exception as e: 
        print(e)

# Update the plot
def realtime_update_plot():
    '''Called at regular intervals by a timer.'''
    global symbol_dict 
    global plots

    # If call is too early
    if all(df.empty for df in symbol_dict.values()):
        return

    # first update all data, then graphics (for zoom rigidity)
    for key in plots:
        plots[key].update_data(symbol_dict[key]['Diff'])   

def make_plot(ax, timeframe):
    ''' Create plots filled with historical data'''

    # For all symbols in the symbol_list
    for symbol in symbol_list:

        # Get historical candles based on timeframe
        if timeframe == '1 day':
            hist_candles = client.get_klines(symbol= symbol, interval='5m', limit=288)
        if timeframe == '1 week':
            hist_candles = client.get_klines(symbol= symbol, interval='1h', limit=168)
        if timeframe == '1 month':
            hist_candles = client.get_klines(symbol= symbol, interval='4h', limit=186)
        if timeframe == '1 year':
            hist_candles = client.get_klines(symbol= symbol, interval='1d', limit=365)

        global symbol_dict 
        df = pd.DataFrame(hist_candles)

        # Only the columns containt the OHLCV data
        df.drop(columns = [1,2,3,5,6,7,8,9,10,11],axis=1,inplace=True)
        df = df.rename(columns={0:"Time", 4:"Close"})

        # Convert time in ms to datetime
        df = df.astype({'Time':'datetime64[ms]','Close':float})
        df.set_index('Time', inplace=True)

        # (new - old) / old * 100
        df['Diff'] = (df['Close'] - df['Close'][0]) / df['Close'][0] * 100

        symbol_dict[symbol] = df

    # create plot
    global plots

    sorted_dict = {}

    # Sort by last diff
    for symbol in symbol_list:
        df = symbol_dict[symbol]
        last = df['Diff'][-1]
        sorted_dict[symbol] = last

    # Sort from highest to lowest
    sorted_dict = dict(sorted(sorted_dict.items(), key=lambda item: item[1], reverse=True))

    counter = 0
    
    # List of hex colors of rainbow
    color_list = rainbow_colors(len(symbol_list))

    # Plot it in rainbow colors depending which symbol's last close diff is the highest
    plots = {}
    for symbol in sorted_dict:
        df = symbol_dict[symbol]
        plots[symbol] = fplt.plot(df['Diff'], ax=ax, legend=symbol, color = color_list[counter])
        counter += 1

def rainbow_colors(n):

    # N less than 2 results in error
    if n < 2:
        return ['#FF0000']

    end=300/360

    color_list = []

    rgb_colors = [colorsys.hls_to_rgb(end * i/(n-1), 0.5, 1) for i in range(n)]

    for color in rgb_colors:
        color = tuple(round(i * 255) for i in color)
        hex = '#%02x%02x%02x' % color
        color_list.append(hex)

    return color_list

def create_ctrl_panel(win):
    panel = QWidget(win)
    panel.move(180, 0)
    win.scene().addWidget(panel)
    layout = QtGui.QGridLayout(panel)

    # Live mode checkbox
    panel.livemode = QRadioButton(panel)
    panel.livemode.setText('Live mode')
    panel.livemode.setChecked(True)
    panel.livemode.setStyleSheet("color: white")
    panel.livemode.toggled.connect(live_mode_toggle)
    layout.addWidget(panel.livemode, 0, 0)

    layout.setColumnMinimumWidth(1, 5)

    # Timeframe
    panel.timeframe = QComboBox(panel)
    [panel.timeframe.addItem(i) for i in '1 day,1 week,1 month,1 year'.split(',')]
    panel.timeframe.setCurrentIndex(0)
    panel.timeframe.currentTextChanged.connect(change_assets)
    layout.addWidget(panel.timeframe, 0, 2)

    layout.setColumnMinimumWidth(3, 5)

    text = QLabel()
    text.setText('Coins')
    text.setStyleSheet("color: white")
    text.move(0,0)
    layout.addWidget(text, 0, 4)

    # Amount of coins, QLineEdit
    # https://doc.qt.io/qt-5/qlineedit.html#signals
    panel.amount = QLineEdit(panel)
    panel.amount.setMaximumWidth(20)
    panel.amount.setText('25')
    panel.amount.textChanged.connect(change_assets)
    layout.addWidget(panel.amount, 0, 6) 

    return panel

def live_mode_toggle(live):

    if (live):
        global bm
        # Start binance socket
        bm.start()

    else:
        # Stop the socket
        bm.stop_socket(key)

        # Cant restart after stopping the socket

# Get top volume dataframe, using pickle or generating new df
top_volume()

# fplt properties
fplt.y_pad = 0.07 # pad some extra (for control panel)
fplt.max_zoom_points = 7
fplt.autoviewrestore()

# Chart title
ax = fplt.create_plot('price Δ', rows=1)
ax.showGrid(True, True)

# Create control panel
ctrl_panel = create_ctrl_panel(ax.vb.win)
change_assets()
live_mode_toggle(True)

# Save the key of this?
key = bm.start_miniticker_socket(ws_response)

# Update graph every 5 seconds, lowering this number can case performance issues
fplt.timer_callback(realtime_update_plot, 5)
fplt.show()
