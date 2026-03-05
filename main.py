import requests
import re
import os
import csv
from datetime import datetime, timedelta

API_KEY = os.getenv("DART_API_KEY")
URL = "https://opendart.fss.or.kr/api/list.json"
DB_FILE = "etf_db.csv"

# 기존 ETF DB 로드
def load_existing_etf():
    if not os.path.exists(DB_FILE):
        return set()
    existing = set()
    with open(DB_FILE, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            existing.add(normalize_name(row['fund_name']))
    return existing

# 이름 정규화
def normalize_name(name):
    name = re.sub(r'\{.*?\}', '', name)
    name = re.sub(r'\([^)]*\)', '', name)
    name = name.strip()
    keyword = "증권상장지수투자신탁"
    if keyword in name:
        name = name[:name.index(keyword) + len(keyword)]
    return name.strip()

# 신규 ETF DB 저장
def append_new_etf(fund_name):
    file_exists = os.path.exists(DB_FILE)
    with open(DB_FILE, 'a', newline='', encoding='utf-8') as f:
        fieldnames = ['fund_name']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            'fund_name': fund_name
        })

# 텔레그램 전송
def send_telegram(message):
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message
    }
    requests.post(url, data=payload)


# ETF 공시 감지
def check_new_etf():
    today = datetime.now()
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
    
    for item in data.get("list", []):
        report_nm = item.get("report_nm", "")
        rcept_dt = item.get("rcept_dt", "")
        if "상장지수" not in report_nm:
            continue
        # 펀드명 추출
        match = re.search(r'\(([^()]*)\)\s*$', report_nm)
        if not match:
            continue
        fund_name = match.group(1)
        fund_name = normalize_name(fund_name)

        if fund_name not in existing_etf:
            date_format = datetime.strptime(rcept_dt, "%Y%m%d").strftime("%Y.%m.%d")
            message = f"{date_format} 접수\n{fund_name}"
            send_telegram(message)
            append_new_etf(fund_name)
            existing_etf.add(fund_name)
            print("NEW ETF:", fund_name)

        else:
            print("Already exists:", fund_name)

# 실행
if __name__ == "__main__":
    check_new_etf()
