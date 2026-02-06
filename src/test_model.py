from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from check_env import code_llm

# 1. 기본적인 코드 생성 프롬프트
code_gen_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert Python programmer. Return ONLY the code inside markdown code blocks. No explanation."),
    ("user", "{task}")
])

code_chain = code_gen_prompt | code_llm | StrOutputParser()

task = "Write a Python function to calculate the N-th Fibonacci number efficiently."
generated_code = code_chain.invoke({"task": task})
print("### 1차 생성된 코드 ###")
print(generated_code)
