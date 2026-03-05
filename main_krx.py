import requests
import os
import csv
import time
from bs4 import BeautifulSoup

URL_KRX = "https://isin.krx.co.kr/corp/corpList.do"
DB_FILE_KRX = "etf_db_krx.csv"


# 기존 ETF DB 로드
def load_existing_etf_krx():
    if not os.path.exists(DB_FILE_KRX):
        return set()

    existing = set()

    with open(DB_FILE_KRX, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            existing.add(row['fund_name'])

    return existing


# 신규 ETF DB 저장
def append_new_etf_krx(fund_name):

    file_exists = os.path.exists(DB_FILE_KRX)

    with open(DB_FILE_KRX, 'a', newline='', encoding='utf-8') as f:

        fieldnames = ['fund_name']
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerow({
            'fund_name': fund_name
        })


# 텔레그램 전송
def send_telegram_krx(message):

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": message
    }

    requests.post(url, data=payload)


# KRX ETF 목록 가져오기
def get_krx_etf_list():

    params = {
        "method": "corpInfoList",
        "searchType": "13",  # 발행기관명
        "searchText": "상장지수"
    }

    res = requests.get(URL_KRX, params=params)
    soup = BeautifulSoup(res.text, "html.parser")

    table = soup.find("table")

    if table is None:
        return []

    rows = table.find_all("tr")[1:]

    etf_list = []

    for row in rows:

        cols = row.find_all("td")

        if len(cols) < 4:
            continue

        fund_name = cols[1].text.strip()
        listing_status = cols[3].text.strip()

        etf_list.append({
            "fund_name": fund_name,
            "listing_status": listing_status
        })

    return etf_list


# 신규 ETF 감지
def check_new_etf_krx():

    existing_etf = load_existing_etf_krx()

    etf_list = get_krx_etf_list()

    for etf in etf_list:

        fund_name = etf["fund_name"]
        listing_status = etf["listing_status"]

        # 비상장 ETF만 체크
        if "비상장" not in listing_status:
            continue

        if fund_name not in existing_etf:

            message = f"신규 ETF 감지 (KRX)\n{fund_name}"

            send_telegram_krx(message)

            append_new_etf_krx(fund_name)

            existing_etf.add(fund_name)

            print("NEW ETF:", fund_name)

        else:

            print("Already exists:", fund_name)

        time.sleep(0.2)


# 실행
if __name__ == "__main__":
    check_new_etf_krx()
