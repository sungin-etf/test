import requests
import re
import os
import csv
from datetime import datetime, timedelta

API_KEY = os.getenv("DART_API_KEY")
URL = "https://opendart.fss.or.kr/api/list.json"
DB_FILE = "etf_db.csv"


# 기존 ETF DB 불러오기
def load_existing_etf():
    if not os.path.exists(DB_FILE):
        return set()

    existing = set()
    with open(DB_FILE, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = f"{row['rcept_dt']}_{row['fund_name']}"
            existing.add(key)

    return existing


# 새 ETF DB 저장
def append_new_etf(rcept_dt, fund_name):
    file_exists = os.path.exists(DB_FILE)

    with open(DB_FILE, 'a', newline='', encoding='utf-8') as f:
        fieldnames = ['rcept_dt', 'fund_name']
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerow({
            'rcept_dt': rcept_dt,
            'fund_name': fund_name
        })


# 텔레그램 발송
def send_telegram(message):
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message
    }

    requests.post(url, data=payload)


# DART 신규 ETF 감지
def check_new_etf():
    today = datetime.today()
    start_date = today - timedelta(days=7)

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

    for item in data.get("list", []):
        report_nm = item.get("report_nm", "")
        rcept_dt = item.get("rcept_dt", "")

        if "상장지수" in report_nm:

            match = re.search(r'\(([^()]*)\)\s*$', report_nm)
            if match:
                fund_name = match.group(1)
                unique_key = f"{rcept_dt}_{fund_name}"

                if unique_key not in existing_etf:
                    # 🔔 알림 발송
                    message = f"""
접수일: {rcept_dt}
ETF명: {fund_name}
"""
                    send_telegram(message)

                    # 📂 DB에 추가 저장
                    append_new_etf(rcept_dt, fund_name)

                    print("NEW ETF:", fund_name)
                else:
                    print("Already exists:", fund_name)


if __name__ == "__main__":
    check_new_etf()
