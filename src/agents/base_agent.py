from __future__ import annotations

import re
from dataclasses import dataclass

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


@dataclass
class AgentConfig:
    base_url: str = "http://localhost:11434"
    code_llm_name: str = "qwen2.5-coder:7b"
    code_temperature: float = 0.1


class BaseCodeAgent:
    """
    공통 역할:
      - Ollama 모델 생성
      - code generation chain 생성
      - reviewer용 llm 제공
      - 코드 블록 추출
    """

    def __init__(self, cfg: AgentConfig):
        self.cfg = cfg

        self.code_llm = ChatOllama(
            model=cfg.code_llm_name,
            temperature=cfg.code_temperature,
            base_url=cfg.base_url
        )

        self.code_gen_prompt = ChatPromptTemplate.from_messages([
            ("system",
             "You are an expert Python programmer. "
             "Return ONLY the code inside markdown code blocks. No explanation."),
            ("user", "{task}")
        ])

        self.code_chain = (
            self.code_gen_prompt
            | self.code_llm
            | StrOutputParser()
        )

    @staticmethod
    def extract_code(text: str) -> str:
        pattern = r"```(?:python)?\s*\n(.*?)```"
        m = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if m:
            return m.group(1).strip()
        return (text or "").replace("```", "").strip()

    def solve_one(self, problem, evaluator):
        raise NotImplementedError
