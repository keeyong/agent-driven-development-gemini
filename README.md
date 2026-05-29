# Gemini AI 영수증 정보 추출기

이 프로젝트는 Google의 Gemini AI(최신 `google-genai` SDK 사용)를 활용하여 자연어 문장에서 영수증 정보(날짜, 장소, 메뉴, 금액)를 추출하고 이를 정형화된 JSON 형태로 반환하는 파이썬 스크립트입니다.

## 사전 준비 (Prerequisites)
- Python 3.8 이상
- Google Gemini API 키 (Google AI Studio에서 발급 가능)

## 1. 가상 환경 설정 및 패키지 설치

시스템 파이썬 환경을 보호하고 패키지 충돌을 막기 위해 **가상 환경(Virtual Environment)** 사용을 권장합니다.

### Mac / Linux
```bash
# 1. 프로젝트 폴더로 이동 후 가상 환경 생성 (폴더명: .venv)
python3 -m venv .venv

# 2. 가상 환경 활성화
source .venv/bin/activate

# 3. 필요한 라이브러리 설치
pip install google-genai
```

### Windows (명령 프롬프트/PowerShell)
```cmd
# 1. 프로젝트 폴더로 이동 후 가상 환경 생성
python -m venv .venv

# 2. 가상 환경 활성화
.venv\Scripts\activate

# 3. 필요한 라이브러리 설치
pip install google-genai
```
*(가상 환경이 활성화되면 프롬프트 앞에 `(.venv)`가 표시됩니다.)*

## 2. API 키 환경 변수 설정

보안을 위해 API 키를 코드 파일에 직접 적지 않고 **환경 변수**로 저장하여 실행합니다.

### 🔹 Mac / Linux (zsh 사용 기준)

현재 터미널 창뿐만 아니라, **새 터미널을 열 때마다 자동으로 적용**되도록 설정하는 방법입니다.

1.  터미널을 열고 셸 설정 파일(보통 `.zshrc`)을 편집기로 엽니다.
    ```bash
    nano ~/.zshrc
    ```
2.  파일 맨 아래에 다음 내용을 추가합니다.
    ```bash
    export GOOGLE_API_KEY="여러분의_실제_API_키"
    ```
3.  `Ctrl + O` (저장), `Enter`, `Ctrl + X` (종료)를 눌러 나옵니다.
4.  설정을 즉시 적용하려면 아래 명령어를 입력하거나 터미널을 새로 엽니다.
    ```bash
    source ~/.zshrc
    ```

### 🔹 Windows (시스템 영구 설정)

한 번 설정하면 **재부팅 후에도 계속 유지**되는 방법입니다.

1.  `시작` 메뉴에서 **'시스템 환경 변수 편집'**을 검색하여 실행합니다.
2.  하단의 **[환경 변수]** 버튼을 클릭합니다.
3.  '사용자 변수' 또는 '시스템 변수' 항목에서 **[새로 만들기]**를 클릭합니다.
4.  다음 정보를 입력하고 [확인]을 누릅니다.
    *   변수 이름: `GOOGLE_API_KEY`
    *   변수 값: `여러분의_실제_API_키`
5.  열려 있는 모든 확인 창을 닫고, **현재 열린 명령 프롬프트나 PowerShell 창을 모두 닫았다가 다시 엽니다.**

---

### 🔹 일시적인 설정 (현재 창에서만)

임시로 테스트할 때만 사용하세요.

*   **Mac/Linux:** `export GOOGLE_API_KEY="키값"`
*   **Windows (CMD):** `set GOOGLE_API_KEY="키값"`
*   **Windows (PowerShell):** `$env:GOOGLE_API_KEY="키값"`

## 3. 코드 실행

가상 환경이 활성화되어 있고 환경 변수가 설정된 상태에서 스크립트를 실행합니다.

```bash
python extract_info_v2.py
```

### 예상 출력 결과
```json
{
  "date": "2026-05-27",
  "location": "강남역 이탈리안 레스토랑",
  "menu": [
    {
      "item": "피자",
      "count": 1
    },
    {
      "item": "파스타",
      "count": 2
    }
  ],
  "total_amount": 45000
}
```

## 코드 수정 (입력 문장 변경)
분석할 문장을 바꾸고 싶다면 `extract_info_v2.py` 파일의 하단 `if __name__ == "__main__":` 부분을 수정하세요.
```python
if __name__ == "__main__":
    input_text = "분석할 새로운 문장을 여기에 입력하세요"
    result = extract_receipt_info(input_text)
    print(json.dumps(result, indent=2, ensure_ascii=False))
```