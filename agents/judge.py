import os
import json
from typing import Union
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    HumanMessagePromptTemplate,
    AIMessagePromptTemplate
)
from langchain.prompts.few_shot import FewShotChatMessagePromptTemplate
from agents.memory_agent import get_memory

load_dotenv()

# BaseModel do juiz
class Judge(BaseModel):
    evaluation: str = Field(
        description='Avaliação final do juiz: "Boa", "Aceitável" ou "Ruim"'
    )

# Modelo chatgpt-4
model = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=os.getenv("OPENAI_API_KEY")
).with_structured_output(Judge)

# Lendo o prompt do juiz
with open("prompts/judge.txt", "r", encoding="utf-8") as x:
    system_text = x.read()
system_prompt = ("system", system_text)

# Lendo os fewshots do juiz
with open("shots/judge_shots.json", "r", encoding="utf-8") as x:
    shots = json.load(x)


example_prompt = ChatPromptTemplate.from_messages([
    HumanMessagePromptTemplate.from_template("{human}"),
    AIMessagePromptTemplate.from_template("{ai}")
])

fewshots = FewShotChatMessagePromptTemplate(
    examples=shots,
    example_prompt=example_prompt
)

# prompt final
judge_prompt = ChatPromptTemplate.from_messages([
    system_prompt,
    fewshots,
    MessagesPlaceholder("memory"), 
    ("human",
     "Contexto:\n{context}\n\nResposta do chatbot:\n{rag_output}\n\nPergunta do usuário:\n{query}\n\nAvalie apenas como 'Boa', 'Aceitável' ou 'Ruim'.")
])

# Pipeline
pipeline = judge_prompt | model 


# Função para rodar o juiz
def judge_agent(query, rag_output, context, session_id):
    """
    Avalia a resposta de um chatbot usando o agente juiz.

    Retorna:
        "Boa", "Aceitável" ou "Ruim"
    """
    try:
        memory = get_memory(session_id)

        output: Judge = pipeline.invoke({
            "query": query,
            "rag_output": rag_output,
            "context": context,
            "memory": memory.messages
        })
        # Retorna avaliação final
        return (True, output.evaluation)

    except Exception as e:
        print(f"Erro no juiz: {e}")
        return (False, "Não foi possível avaliar a resposta.")
    