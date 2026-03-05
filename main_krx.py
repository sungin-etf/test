import requests
import os
import csv
from bs4 import BeautifulSoup

URL_KRX = "https://isin.krx.co.kr/corp/corpList.do"
DB_FILE_KRX = "etf_db_krx.csv"


# -------------------------------
# 기존 ETF DB 로드
# -------------------------------
def load_existing_etf_krx():
    if not os.path.exists(DB_FILE_KRX):
        return set()

    existing = set()

    with open(DB_FILE_KRX, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            existing.add(row["fund_name"])

    return existing


# -------------------------------
# DB 저장
# -------------------------------
def append_new_etf_krx(fund_name):
    file_exists = os.path.exists(DB_FILE_KRX)

    with open(DB_FILE_KRX, "a", newline="", encoding="utf-8") as f:
        fieldnames = ["fund_name"]

        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerow({
            "fund_name": fund_name
        })


# -------------------------------
# 텔레그램 전송
# -------------------------------
def send_telegram(message):

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": message
    }

    requests.post(url, data=payload)


# -------------------------------
# ETF 수집 (KRX)
# -------------------------------
def collect_etf_krx():

    etf_list = []

    for page in range(1, 50):

        params = {
            "method": "corpInfoList",
            "searchWord": "상장지수",
            "paramSearchWord": "상장지수",
            "isur_cd": "",
            "currentPage": str(page),
            "pageIndex": str(page)
        }

        res = requests.post(URL_KRX, data=params)

        soup = BeautifulSoup(res.text, "html.parser")

        rows = soup.select("table tbody tr")

        for r in rows:

            cols = r.find_all("td")

            if len(cols) > 1:

                name = cols[1].text.strip()

                # 운용사 제거
                fund_name = name.split(maxsplit=1)[1]

                etf_list.append(fund_name)

    return etf_list


# -------------------------------
# 신규 ETF 감지
# -------------------------------
def check_new_etf_krx():

    existing = load_existing_etf_krx()

    etf_list = collect_etf_krx()

    for fund_name in etf_list:

        if fund_name not in existing:

            send_telegram(fund_name)

            append_new_etf_krx(fund_name)

            existing.add(fund_name)

            print("NEW:", fund_name)

        else:

            print("EXIST:", fund_name)


# -------------------------------
# 실행
# -------------------------------
if __name__ == "__main__":
    check_new_etf_krx()
