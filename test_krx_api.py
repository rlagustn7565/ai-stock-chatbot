import httpx
import json
from datetime import datetime

api_key = "EA437F5CBDD9438BB91C841144AEA77023EF5A9F"
base_date = datetime.now().strftime("%Y%m%d")
url = "https://data-dbg.krx.co.kr/svc/apis/idx/kospi_dd_trd"

print("=== KRX API 테스트 (SSL 검증 비활성화) ===\n")

# 방식 1: Header X-API-Key
print("1️⃣ 방식 1: Header X-API-Key")
try:
    response = httpx.get(url, params={"basDd": base_date}, headers={"X-API-Key": api_key}, timeout=10, verify=False)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 성공! 데이터: {json.dumps(data, ensure_ascii=False, indent=2)[:500]}")
    else:
        print(f"❌ 실패: {response.text[:200]}")
except Exception as e:
    print(f"❌ 에러: {str(e)}")

print("\n2️⃣ 방식 2: Query parameter apiKey (대문자)")
try:
    response = httpx.get(url, params={"basDd": base_date, "apiKey": api_key}, timeout=10, verify=False)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 성공! 데이터: {json.dumps(data, ensure_ascii=False, indent=2)[:500]}")
    else:
        print(f"❌ 실패: {response.text[:200]}")
except Exception as e:
    print(f"❌ 에러: {str(e)}")

print("\n3️⃣ 방식 3: Query parameter api_key (소문자+언더스코어)")
try:
    response = httpx.get(url, params={"basDd": base_date, "api_key": api_key}, timeout=10, verify=False)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 성공! 데이터: {json.dumps(data, ensure_ascii=False, indent=2)[:500]}")
    else:
        print(f"❌ 실패: {response.text[:200]}")
except Exception as e:
    print(f"❌ 에러: {str(e)}")

print("\n4️⃣ 방식 4: 인증 없이 시도")
try:
    response = httpx.get(url, params={"basDd": base_date}, timeout=10, verify=False)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(f"✅ 인증 없이도 성공!")
    else:
        print(f"❌ 실패: {response.text[:200]}")
except Exception as e:
    print(f"❌ 에러: {str(e)}")
