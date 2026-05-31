import os
import requests
import torch
from typing import Any, List, Optional
from datasets import load_dataset
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.language_models.llms import LLM

class HuggingFaceLlama3LLM(LLM):
    # Pydantic 필드로 명시적 선언
    repo_id: str = "meta-llama/Llama-3.2-1B-Instruct"
    api_url: str = "https://router.huggingface.co/v1/chat/completions"
    
    @property
    def token(self) -> str:
        t = os.getenv("HUGGINGFACEHUB_API_TOKEN")
        if not t:
            raise ValueError("HUGGINGFACEHUB_API_TOKEN 환경 변수가 설정되지 않았습니다.")
        return t

    @property
    def _llm_type(self) -> str:
        return "huggingface_llama3_api"

    def _call(self, prompt: str, stop: Optional[List[str]] = None, **kwargs: Any) -> str:
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.repo_id,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant. Answer based on the info provided."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 512,
            "temperature": 0.1
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=90)
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"].strip()
            return f"Error ({response.status_code}): {response.text}"
        except Exception as e:
            return f"Exception: {str(e)}"

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

def build_rag_system(dataset_size=5000):
    print(f"1. Loading Dataset (Dolly-15k, size={dataset_size})...")
    dataset = load_dataset("databricks/databricks-dolly-15k", split=f"train[:{dataset_size}]")

    print("2. Converting Documents...")
    documents = []
    for e in dataset:
        content = f"Topic: {e['instruction']}\nInfo: {e['context'] if e['context'] else e['response']}"
        documents.append(Document(page_content=content))

    device = "mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu"
    print(f"3. Loading Local Embeddings (Device: {device})...")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-mpnet-base-v2",
        model_kwargs={'device': device}
    )

    print("4. Building FAISS Vector DB...")
    vector_db = FAISS.from_documents(documents, embeddings)
    
    # 클래스 속성 대신 직접 문자열을 사용하거나 인스턴스 후 접근하도록 수정
    print(f"5. Setting up LLM (Llama-3.2-1B-Instruct)...")
    llm = HuggingFaceLlama3LLM()

    print("6. Creating LCEL Pipeline...")
    prompt = PromptTemplate.from_template("Answer the question using this info:\n\n{context}\n\nQuestion: {question}\nAnswer:")

    def debug_retrieval(docs):
        print("\n🔍 [Vector DB 검색된 지식]")
        for i, d in enumerate(docs):
            print(f"[{i+1}]: {d.page_content[:150]}...")
        return docs

    rag_chain = (
        {"context": vector_db.as_retriever(search_kwargs={"k": 3}) | debug_retrieval | format_docs, 
         "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    return rag_chain

if __name__ == "__main__":
    try:
        rag = build_rag_system()
        print("\n✅ RAG READY! (exit 입력 시 종료)")
        
        while True:
            query = input("\n[질문 입력]: ").strip()
            if not query: continue
            if query.lower() in ['exit', 'quit']: break
            
            print("Thinking...")
            response = rag.invoke(query)
            print(f"\nA: {response}")
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"\n시스템 오류: {e}")
