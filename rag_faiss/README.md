# Dolly-15k FAISS RAG System

HuggingFace의 **Databricks Dolly-15k** 데이터셋과 **FAISS** 벡터 데이터베이스를 활용하여 구축한 RAG(Retrieval-Augmented Generation) 시스템입니다. 베이스 LLM으로는 **Google Flan-T5 XXL**을 사용하여 도메인 지식 기반의 답변을 생성합니다.

## 🌟 주요 특징
- **데이터셋**: `databricks/databricks-dolly-15k` (Instruction, Context 기반 지식 추출)
- **Vector DB**: `FAISS` (고속 유사도 검색)
- **Embeddings**: `sentence-transformers/all-mpnet-base-v2`
- **LLM**: `google/flan-t5-xxl` (HuggingFace Inference API 사용)
- **Framework**: `LangChain` (LCEL 기반의 선언적 파이프라인)

## 📋 사전 요구 사항
- Python 3.9 이상
- HuggingFace API Token ([발급받기](https://huggingface.co/settings/tokens))

## 🚀 시작하기

### 1. 가상 환경 생성 및 활성화
환경 충돌을 방지하기 위해 가상 환경 사용을 권장합니다. (Python 3.12 권장)
```bash
# 가상 환경 생성
python3 -m venv venv

# 가상 환경 활성화 (macOS/Linux)
source venv/bin/activate

# 가상 환경 활성화 (Windows)
# venv\Scripts\activate
```

### 2. 라이브러리 설치
```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정
터미널에서 HuggingFace API 토큰을 설정합니다.
```bash
export HUGGINGFACEHUB_API_TOKEN="your_huggingface_token_here"
```

### 3. 시스템 실행
```bash
python rag_faiss.py
```

## 🛠️ 시스템 구조
1. **Data Ingestion**: Dolly 데이터셋을 로드하고 지식 문서(Document) 객체로 변환합니다.
2. **Indexing**: 임베딩 모델을 사용하여 텍스트를 벡터로 변환 후 FAISS 인덱스에 저장합니다.
3. **Retrieval**: 사용자의 질문과 가장 유사한 컨텍스트 3개를 검색합니다.
4. **Generation**: 검색된 컨텍스트와 질문을 결합한 프롬프트를 Flan-T5 모델에 전달하여 최종 답변을 생성합니다.

## 💡 참고 사항
- `flan-t5-xxl` 모델은 크기가 커서 무료 API 환경에서 호출이 제한될 수 있습니다. 만약 오류가 발생한다면 `rag_faiss.py` 파일 내의 `model_id`를 아래 모델 중 하나로 변경하여 테스트해 보세요:
  - `google/flan-t5-large` (안정적)
  - `google/gemma-2-2b-it` (최신 경량 모델)

## 📄 파일 구성
- `rag_faiss.py`: 메인 소스 코드
- `requirements.txt`: 의존성 라이브러리 목록
- `README.md`: 프로젝트 설명서
