# Binance Line Chart
[![Python 3.8](https://img.shields.io/badge/python-3.8-blue.svg)](https://www.python.org/downloads/release/python-380/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![MIT License](https://img.shields.io/github/license/StephanAkkerman/Binance_Line_Chart.svg?color=brightgreen)](https://opensource.org/licenses/MIT)

---

## Features
The user can choose to turn 'live mode' on or off, the live data is fetched using the Binance API websocket. 

Currently there are 4 time frames avaible, these are:
- 1 day
- 1 week
- 1 month
- 1 year

You can fill in how many lines / coins you want to have displayed, the default is 25.

## Dependencies
The required packages to run this code can be found in the `requirements.txt` file. To run this file, execute the following code block:
```
$ pip install -r requirements.txt 
```
Alternatively, you can install the required packages manually like this:
```
$ pip install <package>
```

## How to run
- Clone the repository
- Run `$ python src/main.py`
- See result

## Screenshots
![1 day 25 coins](https://github.com/StephanAkkerman/Binance_Line_Chart/blob/main/img/1day.png)
![1 month 25 coins](https://github.com/StephanAkkerman/Binance_Line_Chart/blob/main/img/1month.png)
