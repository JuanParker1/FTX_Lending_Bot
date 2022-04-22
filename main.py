import hmac
import os
import schedule
import numpy as np
import time
import pandas as pd
from datetime import datetime
from requests import Request, Session
from client import FtxClient

API_KEY = "RoNMJDIoW8jj0xpOfi8C0EDpXonxlriUCdG5ypdg"
API_SECRET = "nYNNSEY0S3sCJ9vuSK_vNfxT7bhBqYxLPyIw1gEx"
Sub_account_name = ''
You_want_to_lend = ["RAY"]
You_want_to_reserve_howmuch = []


balances = "https://ftx.com/api/wallet/balances"   # 取得錢包
Post_lend = "https://ftx.com/api/spot_margin/offers"  # Post_lend

ftx_client = FtxClient(
    api_key = API_KEY,
    api_secret = API_SECRET
)

if not You_want_to_reserve_howmuch:                                                     ## 保留金額 = [] 都沒輸入，幫你都填上0
    You_want_to_reserve_howmuch = np.zeros(shape=len(You_want_to_lend), dtype=int)
elif len(You_want_to_reserve_howmuch) != len(You_want_to_lend):                         ## 保留金額和要放貸的幣種對不上，警告後停止
    print("Error:Number of You_want_to_lend doesn't match You_want_to_reserve_howmuch")
    os._exit(0)
elif "" in You_want_to_reserve_howmuch:                                                 ## 保留金額和要放貸的幣種對上，但內容為""，全部填0
    You_want_to_reserve_howmuch = np.array(You_want_to_reserve_howmuch)
    You_want_to_reserve_howmuch[You_want_to_reserve_howmuch=='']=0
    You_want_to_reserve_howmuch = You_want_to_reserve_howmuch.astype(np.float64)




def Start():
    for coin,reserve_num in zip(You_want_to_lend,You_want_to_reserve_howmuch): ##指定coin輪流post出去
        print(organize(coin,reserve_num))
    return print("End!")

def organize(coin,reserve_num):
    now_unix = datetime.now()
    now_time = now_unix.strftime("%Y/%m/%d-%H:%M:%S")
    # 取得錢包內可放放貸餘額
    Balance = Get_Balances(coin)
    # 丟給FTX要放貸的訊息
    lending = Submit_lend(coin,Balance,reserve_num)
    # 確認有無放貸成功
    return f"Current time : {now_time}\nYou can lend {coin} the maximum number:{Balance}\n{lending}"

def Get_Balances(coin):
        try:
            Wallet_all_result = ftx_client.get_balances()
            DataFrame_wallet = pd.DataFrame(Wallet_all_result)
            DataFrame_wallet.set_index('coin', inplace=True)    ## 全部有餘額的幣種矩陣
            coin_num = DataFrame_wallet.loc[coin]["total"]      ##  抓到指定coin的數量
            return coin_num
        except Exception as e:
            print(f'Error making order request: {e}')


def Submit_lend(coin,Balance,reserve_num):
    lend_num = Balance - reserve_num
    if lend_num < 0:
        lend_num = 0
    coin_size_rate = {"coin": coin, "size": lend_num, "rate": 0.000001}
    request = Request('POST',Post_lend , json = coin_size_rate)
    send_back = Request_to_FTX(request)

    # print(send_back)
    # print(send_back["success"])
    # if send_back["success"] != True:
    #     print(send_back["error"])
    return f"You lending number:{lend_num}\nState:{send_back}"

def Request_to_FTX(request):
    ts = int(time.time() * 1000)
    prepared = request.prepare()
    signature_payload = f'{ts}{prepared.method}{prepared.path_url}'.encode()

    if prepared.body:
        signature_payload += prepared.body # 終於懂了，這邊是要post放貸資料時，body = {"coin":"RAY", "size":1, "rate":0.000001}
    signature_payload = signature_payload
    signature = hmac.new(API_SECRET.encode(), signature_payload, 'sha256').hexdigest()


    prepared.headers['FTX-KEY'] = API_KEY
    prepared.headers['FTX-SIGN'] = signature
    prepared.headers['FTX-TS'] = str(ts)
    if len(Sub_account_name) > 0 :
        prepared.headers['FTX-SUBACCOUNT'] = Sub_account_name

    s = Session()
    From_FTX = s.send(prepared)

    return From_FTX.json()




Start()
schedule.every(1).hours.do(Start)

while True:
    schedule.run_pending()
    time.sleep(1)



