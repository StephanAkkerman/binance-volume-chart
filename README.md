# Setup
This project uses finplot to graph the lines of the coins and the data is gathered using the Binance API.

# Features
Finding the top volume tickers on Binance is hard to do, since there is no API function for that. 
So the first time loading will take longer, however the data used is saved.
After 24h the data will be fetched again, to get the most actual top volume available.
The user can choose to turn 'live mode' on or off, the live data is fetched using the Binance API websocket. 

Currently there are 4 time frames avaible, these are:
- 1 day
- 1 week
- 1 month
- 1 year

You can fill in how many lines / coins you want to have displayed, the default is 25.

# Screenshots
![1 day 25 coins](https://github.com/StephanAkkerman/Binance_Line_Chart/blob/main/screenshot/1day.png)
![1 month 25 coins](https://github.com/StephanAkkerman/Binance_Line_Chart/blob/main/screenshot/1month.png)
