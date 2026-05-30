from langchain_groq import ChatGroq
# from langchain_openai import OpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

MAX_SUMMARY_TEXT = 6000

llm = ChatGroq(model='llama-3.1-8b-instant', temperature=0)
# llm = OpenAI(model='gpt-4o-mini', temperature=0)

SUMMARY_PROMPT = ChatPromptTemplate.from_messages([
    ('system', '''You are a regulatory compliance analyst. Read the circular and write a concise plain English summary for a non lawyer business executive.

    Rules:
    - Maximum 5 sentences
    - Lead with WHAT is changing or being mandated
    - State WHO is affected (all banks, NBFCs, mutual funds, etc.) 
    - State WHEN it takes effect if a date is mentioned 
    - Zero legal jargon'''),
    ('human', 'Circular title: {title}\n\nFull text:\n{text}\n\nSummary:'), 
    ]) 

parser = StrOutputParser()

summarize_chain = SUMMARY_PROMPT | llm | parser

def summarize_circular(title: str, text: str) -> str:
    return summarize_chain.invoke({
        'title': title, 
        'text': text[:MAX_SUMMARY_TEXT]
    })