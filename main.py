from selenium import webdriver
from selenium.webdriver.common.by import By
from KeepAlive import keep_alive
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC

import pandas as pd
import os
import sys
import time
import pytz
import logging
import requests
import schedule
import psutil
import datetime

chat_id = os.environ['ID']
Api = os.environ['API']
keep_alive()

chrome_options = Options()
#chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome(options=chrome_options)

def dextool_trend(z):
    urls = []
    token_home = []
    data = ""
    try:

        driver.get('https://www.dextools.io/app/en/pairs')
        driver.implicitly_wait(10)

        modal = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "/html/body/ngb-modal-window[1]/div/div/app-video-yt-modal/div[1]/div/h5"))).text
        print(modal)

        if modal == "WELCOME TO DEXTOOLS":
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.XPATH, "/html/body/ngb-modal-window[1]/div/div/app-video-yt-modal/div[1]/button"))).send_keys(Keys.RETURN)
            print("successfully removed modal")

        time.sleep(5)

        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "/html/body/app-root/div/div/main/app-new-home/app-layout/div/div[1]/div[3]/app-hotpairs-list-dashboard")))

        driver.execute_script("arguments[0].scrollIntoView();", element)
        text = []
        for j in range(1,10):
            token = WebDriverWait(driver, 20).until(
        EC.visibility_of_element_located((By.XPATH,
             f"/html/body/app-root/div/div/main/app-new-home/app-layout/div/div[1]/div[3]/app-hotpairs-list-dashboard/div/div[2]/app-carousel/div/div[2]/ul/app-carousel-item/li/div/app-hot-pairs-list/div/app-hot-pairs/ul/li[{j}]/a")))
            text_token = token.text
            text_token = text_token.split("\n")
            text.append(text_token)
            href = token.get_attribute("href")
            token_info = WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.XPATH, f"//app-hot-pairs/ul/li[{j}]"))).text
            token_info = token_info.split()
            urls.append(href)
            token_home.append(token_info)
        
        #print(urls)
        #print(len(token_home))
        df = pd.DataFrame(text, columns=["Number", "Token", "Price", "Gain"])
        if z == "dataframe":
            #print(df)
            return df
        for i in range(0, 5):
            driver.get(urls[i])
            time.sleep(5)
            try:
                WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.XPATH,"//app-pool-info/div/button"))).click()
                time.sleep(2)
                detail = WebDriverWait(driver, 20).until(
                    EC.visibility_of_element_located((By.XPATH,"/html/body/app-root/div/div/main/app-pairexplorer/app-layout/div/div[2]/div[2]/div[1]/div[2]/div/app-pool-info/div"))).text
                # Split the text into lines and extract the values
                detail_list = detail.split("\n")
                #print(detail_list)
                l = 0
                data1 = ""
                emojis = ["💧", "📈", "📆", "💎", "📝", "🛖", "🚧","🗿"]
                for j, elem in enumerate(detail_list):
                    if j % 2 == 0 and "Pooled" not in elem and "Supply" not in elem and "tx" not in elem and "ETH" not in elem and elem != "MCap": 
                        data1 += f"{emojis[l]} {detail_list[j]}{detail_list[j+1]} \n"
                        l+=1
                #print(data1)
            except TimeoutException:
                print(f"Timed out waiting for element {i} to become visible")
        
            if i < len(token_home):
                info = f"Trending on Dextool {token_home[i][0]} Token Name : [{token_home[i][1]}]({urls[i]}) \n💸 Price: {token_home[i][2]} \n📈 1h volume: {token_home[i][3]} \n{data1}"
                data += f"{info} \n"
            else:
                print("Invalid index or empty list")

        #print(data)
        if z == "data":
            return data

    except Exception as e:
        print(e)
            
        
def restart_program():
    """Restarts the current program, with file objects and descriptors
       cleanup
    """
    try:
        p = psutil.Process(os.getpid())
        for handler in p.open_files() + p.connections():
            os.close(handler.fd)
    except Exception as e:
        logging.error(e)

    python = sys.executable
    os.execl(python, python, *sys.argv)


def send_telegram_message(token, chat_id, message):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": 'Markdown'
    }
    response = requests.post(url, json=payload)
    if response.status_code != 200:
        print("Failed to send Telegram message")


def my_task(z):
    try:
        now_utc = datetime.datetime.utcnow()
        ethiopia_tz = pytz.timezone('Africa/Addis_Ababa')
        now_eastern = now_utc.replace(tzinfo=pytz.utc).astimezone(ethiopia_tz)
        ethio_time = now_eastern.strftime("%Y-%m-%d %H:%M:%S ")
        message = dextool_trend(z)
        if message is not None:
            data = f"DEXtool trending @ {ethio_time}\n{message}"
            print(data)
            send_telegram_message(Api, chat_id, data)
            print("You have successfully send a message....")
    except Exception as e:
        print(e)
        restart_program()

def data():
    my_task("data")

def data_frame():
    my_task("dataframe")

#Running the function and scheduling for a specified time
data()
schedule.every(12).minutes.do(data_frame)
schedule.every(30).minutes.do(data)
while True:
    schedule.run_pending()
    time.sleep(1)