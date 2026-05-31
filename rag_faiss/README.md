# Dolly-15k FAISS RAG System

HuggingFace의 **Databricks Dolly-15k** 데이터셋과 **FAISS** 벡터 데이터베이스를 활용하여 구축한 RAG(Retrieval-Augmented Generation) 시스템입니다. 베이스 LLM으로는 **Meta Llama-3.2-1B-Instruct**를 사용하여 도메인 지식 기반의 답변을 생성합니다.

## 🌟 주요 특징
- **데이터셋**: `databricks/databricks-dolly-15k` (Instruction, Context 기반 지식 추출)
- **Vector DB**: `FAISS` (고속 유사도 검색)
- **Embeddings**: `sentence-transformers/all-mpnet-base-v2` (로컬 가속 임베딩)
- **LLM**: `meta-llama/Llama-3.2-1B-Instruct` (HuggingFace Router API 사용)
- **Framework**: `LangChain` (LCEL 기반의 선언적 파이프라인)

## 📋 사전 요구 사항
- Python 3.9 이상
- HuggingFace API Token ([발급받기](https://huggingface.co/settings/tokens))

## 🚀 시작하기

### 1. 환경별 설정

#### A. 로컬 환경 (Mac/Linux/Windows)
환경 충돌을 방지하기 위해 가상 환경 사용을 권장합니다. (Python 3.12 권장)
```bash
# 가상 환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 라이브러리 설치
pip install -r requirements.txt
```

#### B. Google Colab 환경 (T4 GPU 권장)
Colab에서 실행 시 아래 명령어를 첫 번째 셀에서 실행하여 GPU 드라이버와 호환성을 맞춥니다.
```bash
!pip install -r requirements.txt
!pip install --upgrade torch torchvision torchaudio
```
*런타임 유형이 **T4 GPU**로 설정되어 있는지 확인하세요.*

### 2. 환경 변수 설정
HuggingFace API 토큰을 시스템 환경 변수로 설정합니다.
```bash
export HUGGINGFACEHUB_API_TOKEN="your_huggingface_token_here"
```

### 3. 시스템 실행
```bash
python rag_faiss.py
```

## ⚡ 하드웨어 가속 (Hardware Acceleration)
본 시스템은 실행 환경에 따라 최적의 가속 장치를 자동으로 선택합니다:
- **NVIDIA GPU (Colab/PC)**: `cuda` 가속 사용
- **Apple Silicon (Mac M1/M2/M3)**: `mps` (Metal Performance Shaders) 가속 사용
- **기본 환경**: `cpu` 모드 사용

## 🛠️ 시스템 구조
1. **Data Ingestion**: Dolly-15k 데이터셋을 로드하고 지식 문서로 변환합니다. (기본 5,000개)
2. **Indexing**: `all-mpnet-base-v2` 모델을 **로컬**로 다운로드하여 벡터 임베딩을 생성한 후 FAISS에 저장합니다.
3. **Retrieval**: 질문과 유사한 지식을 검색합니다.
4. **Generation**: `meta-llama/Llama-3.2-1B-Instruct` 모델(API)을 사용하여 최종 답변을 생성합니다.

## 💡 참고 사항
- 본 시스템은 HuggingFace의 무료 서버리스 라우터 API(`router.huggingface.co/v1`)를 사용합니다. 무료 티어에서 가장 응답성이 좋고 안정적인 `Llama-3.2-1B-Instruct` 모델을 기본으로 채택하였습니다.
- 성능 향상을 위해 3B 이상의 모델로 변경하고 싶으시다면, 유료 API(PRO)를 구독하시거나 로컬 GPU를 활용한 다운로드 방식으로 코드를 변경하여 사용하실 수 있습니다.

## 📄 파일 구성
- `rag_faiss.py`: 메인 소스 코드
- `requirements.txt`: 의존성 라이브러리 목록
- `README.md`: 프로젝트 설명서
