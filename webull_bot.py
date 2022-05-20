from webull import webull

import json
import webull_config
import yfinance as yf
import pandas as pd
import logging
import os
from tqdm import trange
from time import sleep


def login():
    login_info = None
    try:
        f = open("token.txt", "r")
        login_info = json.load(f)
    except:
        print("First time login.")

    if not login_info:
        wb.get_mfa(webull_config.EMAIL)  # mobile number should be okay as well.
        code = input('Enter MFA Code : ')
        login_info = wb.login(webull_config.EMAIL, webull_config.PASSWORD, 'macbook', code, webull_config.QUESTION_ID,
                              webull_config.QUESTION_ANSWER)  # MFA needs email code entered
        f = open("token.txt", "w")
        f.write(json.dumps(login_info))
        f.close()
    else:
        wb.refresh_login()
        login_info = wb.login(webull_config.EMAIL, webull_config.PASSWORD)


def info():
    position_list = wb.get_positions()
    print("Current Positions:")
    for stock in position_list:
        print("   {} quantity: {} profit/loss: {}".format(stock['ticker']['symbol'], stock['position'],
                                                          stock['unrealizedProfitLoss']))

    account_info = wb.get_account()
    print("\nCash balance: ${}".format(
        account_info['accountMembers'][1]['value']))  # this gets 'cashBalance' from account info


def trade(transaction, symbol, quantity):
    wb.get_account_id()
    wb.get_trade_token(webull_config.TRADING_PIN)
    print(wb.place_order(symbol, action=transaction, quant=quantity, orderType='MKT', enforce='DAY'))


def practice_trade(transaction, symbol):
    wb.get_account_id()
    wb.get_trade_token(webull_config.TRADING_PIN)
    return wb.place_order(symbol, action=transaction, quant=2, orderType='MKT', enforce='DAY')


def MACDBuy(df):
    df['MACDBuy'] = df.Close.ewm(span=12).mean() - df.Close.ewm(span=26).mean()
    df['signalBuy'] = df.MACDBuy.ewm(span=9).mean()


def MACDSell(df):
    df['MACDSell'] = df.Close.ewm(span=12).mean() - df.Close.ewm(span=26).mean()
    df['signalSell'] = df.MACDSell.ewm(span=9).mean()


def get_position():
    wb.refresh_login()
    login_info = wb.login(webull_config.EMAIL, webull_config.PASSWORD)
    position_list = wb.get_positions()
    if len(position_list) != 0 and float(position_list[0]['position']) > 0:
        return True
    else:
        return False


wb = webull()
login()

os.system('clear')
logging.basicConfig(filename="stock_transactions.log", level=logging.INFO, format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p')
print('Trading bot starting...\n\n')
in_position = get_position()
print('In Position on start: ' + str(in_position) + '\n')

while 1:
    for i in trange(720):
        try:
            historical = yf.download('UPST', start=pd.Timestamp.now() - pd.Timedelta(days=1), interval='1m',
                                     progress=False, prepost=True)
            MACDBuy(historical)
            MACDSell(historical)
            in_position = get_position()

            # # Buy code
            if historical['MACDBuy'].iloc[-1] > historical['signalBuy'].iloc[-1] and not in_position:
                logging.info(practice_trade('BUY', 'UPST'))

            # # Sell code
            elif historical['MACDSell'].iloc[-1] < historical['signalSell'].iloc[-1] and in_position:
                logging.info(practice_trade('SELL', 'UPST'))
            sleep(60)

        except Exception as e:
            print(str(e))
            sleep(1)
