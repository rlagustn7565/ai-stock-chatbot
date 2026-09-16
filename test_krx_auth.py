import httpx
import json
from datetime import datetime

api_key = "EA437F5CBDD9438BB91C841144AEA77023EF5A9F"
base_date = datetime.now().strftime("%Y%m%d")
url = "https://data-dbg.krx.co.kr/svc/apis/idx/kospi_dd_trd"

print("=== KRX API 테스트 (AUTH_KEY 헤더) ===\n")

# 테스트 1: httpx 기본 방식
print("1️⃣ httpx 기본 방식 (verify=False)")
try:
    headers = {
        "AUTH_KEY": api_key,
        "Content-Type": "application/json"
    }
    params = {"basDd": base_date}

    with httpx.Client(verify=False) as client:
        response = client.get(url, params=params, headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Request URL: {response.request.url}")
        print(f"Request Headers: {dict(response.request.headers)}")
        print(f"Response: {response.text[:200]}")

except Exception as e:
    print(f"❌ 에러: {str(e)}")

# 테스트 2: requests 라이브러리
print("\n2️⃣ requests 라이브러리로 비교")
try:
    import requests
    headers = {
        "AUTH_KEY": api_key,
        "Content-Type": "application/json"
    }
    params = {"basDd": base_date}

    response = requests.get(url, params=params, headers=headers, verify=False)
    print(f"Status: {response.status_code}")
    print(f"Request URL: {response.request.url}")
    print(f"Request Headers: {dict(response.request.headers)}")
    print(f"Response: {response.text[:200]}")

except Exception as e:
    print(f"❌ 에러: {str(e)}")

# 테스트 3: curl 명령어 (PowerShell)
print("\n3️⃣ curl 명령어 확인")
print(f'curl -X GET "{url}?basDd={base_date}" -H "AUTH_KEY: {api_key}"')
