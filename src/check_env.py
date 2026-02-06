# 기본 설정
import os
from langchain_ollama import ChatOllama, OllamaEmbeddings

# Ollama가 실행 중인 서버 URL
BASE_URL = "http://localhost:11434"

# 💡 모델 선택
# - llama3.1: 일반적인 대화와 추론을 잘함 (문과생 느낌)
# - qwen2.5-coder: 코딩을 기가 막히게 잘함 (이과생 느낌)
LLM_NAME = "llama3.1:8b"
CODE_LLM_NAME = "qwen2.5-coder:7b"

# LangChain LLM 인스턴스 생성
llm = ChatOllama(
    model=LLM_NAME,
    temperature=0,
    base_url=BASE_URL
)

code_llm = ChatOllama(
    model=CODE_LLM_NAME,
    temperature=0.1,
    base_url=BASE_URL
)

embedding = OllamaEmbeddings(model="nomic-embed-text", base_url=BASE_URL)

print(f"준비 완료! 대화용 모델: {LLM_NAME}, 코딩용 모델: {CODE_LLM_NAME}")