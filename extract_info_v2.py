from google import genai
import json
import os
from datetime import datetime

# 1. 환경 변수에서 API 키 로드
api_key = os.environ.get("GOOGLE_API_KEY")

if not api_key:
    print(json.dumps({"error": "GOOGLE_API_KEY 환경 변수가 설정되지 않았습니다."}, ensure_ascii=False))
    exit(1)

# 2. 클라이언트 설정
try:
    client = genai.Client(api_key=api_key)
except Exception as e:
    print(json.dumps({"error": f"클라이언트 생성 실패: {str(e)}"}, ensure_ascii=False))
    exit(1)

def extract_receipt_info(text):
    current_date = datetime.now().strftime("%Y-%m-%d")

    prompt = f"""
    입력된 문장에서 날짜, 장소, 메뉴, 금액을 추출하여 JSON 형식으로 응답해줘.
    오늘 날짜가 {current_date}임을 참고해서 '어제', '오늘' 등은 실제 날짜로 계산해줘.

    입력 문장: "{text}"

    응답 형식:
    {{
      "date": "YYYY-MM-DD",
      "location": "장소명",
      "menu": [
        {{"item": "메뉴명", "count": 수량}}
      ],
      "total_amount": 금액(숫자)
    }}
    """

    try:
        # 최신 SDK 방식
        response = client.models.generate_content(
            model='gemini-flash-latest',
            contents=prompt,
            config={
                'response_mime_type': 'application/json'
            }
        )
        return json.loads(response.text)
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    input_text = "강남역 이탈리안 레스토랑에서 45,000원 주고 어제 피자 1개랑 파스타 2개 먹었네"
    result = extract_receipt_info(input_text)
    print(json.dumps(result, indent=2, ensure_ascii=False))
