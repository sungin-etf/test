import requests
import re
import os
import csv
from datetime import datetime, timedelta

API_KEY = os.getenv("DART_API_KEY")
URL = "https://opendart.fss.or.kr/api/list.json"
DB_FILE = "etf_db.csv"

# -------------------------------
# 기존 ETF DB 불러오기
# -------------------------------
def load_existing_etf():
    if not os.path.exists(DB_FILE):
        return set()
    existing = set()
    with open(DB_FILE, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            existing.add(row['fund_name'].strip())
    return existing

# -------------------------------
# 새 ETF DB 저장
# -------------------------------
def append_new_etf(fund_name):
    file_exists = os.path.exists(DB_FILE)
    with open(DB_FILE, 'a', newline='', encoding='utf-8') as f:
        fieldnames = ['fund_name']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow({'fund_name': fund_name})

# -------------------------------
# 텔레그램 발송
# -------------------------------
def send_telegram(message):
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not bot_token or not chat_id:
        print("Telegram 환경변수가 설정되지 않았습니다.")
        return

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    try:
        resp = requests.post(url, data=payload)
        if resp.status_code != 200:
            print("Telegram 발송 실패:", resp.text)
    except Exception as e:
        print("Telegram 전송 중 예외 발생:", e)

# -------------------------------
# DART 신규 ETF 감지 및 알림
# -------------------------------
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

    try:
        res = requests.get(URL, params=params)
        res.raise_for_status()
        data = res.json()
    except Exception as e:
        print("DART API 호출 오류:", e)
        return

    existing_etf = load_existing_etf()
    new_count = 0

    for item in data.get("list", []):
        report_nm = item.get("report_nm", "")
        rcept_dt = item.get("rcept_dt", "")

        if "상장지수" in report_nm:
            match = re.search(r'\(([^()]*)\)\s*$', report_nm)
            if match:
                fund_name = match.group(1).strip()

                # DB에 없는 경우만 발송 + 추가
                if fund_name not in existing_etf:
                    message = f"📌 신규 ETF 감지\n접수일: {rcept_dt}\nETF명: {fund_name}"
                    send_telegram(message)
                    append_new_etf(fund_name)
                    existing_etf.add(fund_name)  # 반복 처리 안전하게
                    new_count += 1
                    print("NEW ETF:", fund_name)
                else:
                    print("Already exists:", fund_name)

    if new_count == 0:
        print("신규 ETF 없음")

# -------------------------------
# 메인 실행
# -------------------------------
if __name__ == "__main__":
    check_new_etf()
