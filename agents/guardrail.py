# Importações
import os
import json
from typing import Union
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    HumanMessagePromptTemplate,
    AIMessagePromptTemplate
)
from langchain.prompts.few_shot import FewShotChatMessagePromptTemplate
from agents.memory_agent import get_memory

# Carrega as envs
load_dotenv()

# BaseModel
class Guardrail(BaseModel):
    flag: int = Field(description="0 se a entrada for válida, 1 se for ofensiva")
    message: Union[str, None] = Field(description="Mensagem educada para fugir do assunto caso flag=1, ou None se flag=0")

# Modelo gemini 2.0 flash lite
model = ChatGoogleGenerativeAI(
    model= "gemini-2.0-flash-lite"
    , temperature= 0.2
    , top_p = 0.95
    , google_api_key = os.getenv("GEMINI_API_KEY")
).with_structured_output(Guardrail)

# Lendo o arquivo guardrail.txt (onde tem o prompt)
with open("prompts/guardrail.txt", "r", encoding="utf-8") as file:
    system_prompt = ("system", file.read())

# Lendo o arquivo guardrail_shots.json (onde tem os few-shots)
with open("shots/guardrail_shots.json", "r", encoding="utf-8") as file:
    shots = json.load(file)

example_prompt = ChatPromptTemplate.from_messages([
    HumanMessagePromptTemplate.from_template("{human}"),
    AIMessagePromptTemplate.from_template("{ai}")
])

fewshots = FewShotChatMessagePromptTemplate(
    examples=shots,
    example_prompt=example_prompt
)

# Prompt final
prompt = ChatPromptTemplate.from_messages([
    system_prompt,
    fewshots,
    MessagesPlaceholder("memory"),
    ("human", "{query}")
])

# Pipeline
pipeline = prompt | model

# Função principal
def guardrail_agent(query, session_id):
    """
    Executa o guardrail para validar a entrada do usuário.

    Retorna:
      (True, None) se a entrada for válida
      (False, mensagem) se for ofensiva/fora do escopo
    """
    try:
        memory = get_memory(session_id)

        output: Guardrail = pipeline.invoke({"query": query, "memory": memory.messages})

        if output.flag == 0:
            return (True, None) 
        else:
            return (False, output.message)

    except Exception as e:
        print(f"Erro no guardrail: {e}")

    return "Não foi possível validar sua pergunta."











