import requests
import re
import os
import csv
from datetime import datetime, timedelta

API_KEY = os.getenv("DART_API_KEY")
URL = "https://opendart.fss.or.kr/api/list.json"
DB_FILE = "etf_db.csv"


def load_existing_etf():
    if not os.path.exists(DB_FILE):
        return set()

    existing = set()
    with open(DB_FILE, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            existing.add(row['fund_name'].strip())

    return existing


def append_new_etf(fund_name):
    file_exists = os.path.exists(DB_FILE)

    with open(DB_FILE, 'a', newline='', encoding='utf-8') as f:
        fieldnames = ['fund_name']
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerow({'fund_name': fund_name})


def send_telegram(message):
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": message
    }

    requests.post(url, data=payload)


def check_new_etf():

    today = datetime.today()
    start_date = today - timedelta(days=1)

    params = {
        "crtfc_key": API_KEY,
        "pblntf_ty": "G",
        "bgn_de": start_date.strftime("%Y%m%d"),
        "end_de": today.strftime("%Y%m%d"),
        "page_no": 1,
        "page_count": 200
    }

    res = requests.get(URL, params=params)
    data = res.json()

    existing_etf = load_existing_etf()
    new_count = 0

    for item in data.get("list", []):

        report_nm = item.get("report_nm", "")
        rcept_dt = item.get("rcept_dt", "")

        if "상장지수" not in report_nm:
            continue

        match = re.search(r'\(([^()]*)\)\s*$', report_nm)

        if not match:
            continue

        fund_name = match.group(1).strip()

        if fund_name not in existing_etf:

            message = f"""📌 신규 ETF 감지
접수일: {rcept_dt}
ETF명: {fund_name}
"""

            send_telegram(message)

            append_new_etf(fund_name)
            existing_etf.add(fund_name)

            new_count += 1

            print("NEW ETF:", fund_name)

        else:
            print("Already exists:", fund_name)

    if new_count == 0:
        print("신규 ETF 없음")


if __name__ == "__main__":
    check_new_etf()
