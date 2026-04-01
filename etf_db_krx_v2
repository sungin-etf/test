import requests
import os
import csv
from bs4 import BeautifulSoup

URL_KRX = "https://isin.krx.co.kr/corp/corpList.do"
DB_FILE_KRX = "etf_db_krx_v2.csv"


# 기존 ETF DB 로드 (issuer_code 기준)
def load_existing_etf_krx():
    if not os.path.exists(DB_FILE_KRX):
        return {}

    existing = {}
    with open(DB_FILE_KRX, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            existing[row["issuer_code"]] = row["fund_name"]

    return existing


# DB 저장
def append_new_etf_krx(issuer_code, fund_name):
    file_exists = os.path.exists(DB_FILE_KRX)

    with open(DB_FILE_KRX, "a", newline="", encoding="utf-8") as f:
        fieldnames = ["issuer_code", "fund_name"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerow({
            "issuer_code": issuer_code,
            "fund_name": fund_name
        })


# 텔레그램 전송
def send_telegram(message):
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        print("텔레그램 환경변수 미설정")
        return

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": message
    }

    try:
        requests.post(url, data=payload, timeout=5)
    except Exception as e:
        print("텔레그램 전송 실패:", e)


# ETF 수집 (issuer_code + fund_name)
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

        if not rows:
            break

        for r in rows:
            cols = r.find_all("td")

            if len(cols) > 1:
                issuer_code = cols[0].text.strip()
                fund_name = cols[1].text.strip()

                if issuer_code:
                    etf_list.append((issuer_code, fund_name))

    return etf_list


# 신규 ETF + 이름 변경 감지
def check_new_etf_krx():
    existing = load_existing_etf_krx()
    etf_list = collect_etf_krx()

    for issuer_code, fund_name in etf_list:

        # 신규 ETF
        if issuer_code not in existing:
            send_telegram(f"[신규 ETF] {fund_name}")
            append_new_etf_krx(issuer_code, fund_name)
            existing[issuer_code] = fund_name
            print("NEW:", issuer_code, fund_name)

        # 이름 변경
        elif existing[issuer_code] != fund_name:
            old_name = existing[issuer_code]
            send_telegram(f"[이름변경] {old_name} → {fund_name}")
            existing[issuer_code] = fund_name
            print("UPDATED:", issuer_code, old_name, "→", fund_name)

        else:
            print("EXIST:", issuer_code, fund_name)


# 실행
if __name__ == "__main__":
    check_new_etf_krx()
