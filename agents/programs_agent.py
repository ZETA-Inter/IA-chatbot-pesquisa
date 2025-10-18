# Importações
from zoneinfo import ZoneInfo
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    HumanMessagePromptTemplate,
    AIMessagePromptTemplate)
from langchain.agents import create_tool_calling_agent , AgentExecutor
from langchain.prompts.few_shot import FewShotChatMessagePromptTemplate
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
import os
from dotenv import load_dotenv
from datetime import datetime
from agents.pg_tools import PROGRAMS_TOOLS
import json

# Carrega as envs
load_dotenv()

# timezone
TZ = ZoneInfo("America/Sao_Paulo")
today = datetime.now(TZ).date()

# dicionário para armazenar o histórico de mensagens 
store = {}
def get_session_history (session_id) -> ChatMessageHistory:
    # Função que retorna o histórico de uma sessão específica
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    
    return store[session_id]

# Modelo Gemini 2.5 flash
llm = ChatGoogleGenerativeAI(
    model= "gemini-2.5-flash"
    , temperature= 0.0
    , top_p = 1.0
    , google_api_key = os.getenv("GEMINI_API_KEY")
)

# Lendo o arquivo programs_agent.txt (onde tem o prompt)
with open ("prompts/programs_agent.txt", "r", encoding="utf-8") as file:
    system_prompt = ("system", file.read())

# Lendo o arquivo programs_shots.json (onde tem os few-shots)
with open ("shots/programs_shots.json", "r", encoding="utf-8") as file:
    shots = json.load(file)

example_prompt = ChatPromptTemplate.from_messages([
    HumanMessagePromptTemplate.from_template("{human}"),
    AIMessagePromptTemplate.from_template("{ai}")
])

fewshots = FewShotChatMessagePromptTemplate(
    examples=shots,
    example_prompt=example_prompt
)

prompt = ChatPromptTemplate.from_messages([
    system_prompt,                          
    fewshots,                                
    MessagesPlaceholder("chat_history"),   
    ("human", "{input}"),
    MessagesPlaceholder("agent_scratchpad")           
])

prompt = prompt.partial(today_local=today.isoformat())

"""Placeholder normal = variavel que precisa ser passada toda vez .
Partial =  pré configuração do template 
"""

agent = create_tool_calling_agent(llm, PROGRAMS_TOOLS, prompt)
agent_executor = AgentExecutor(agent=agent, tools=PROGRAMS_TOOLS, verbose=False)


chain = RunnableWithMessageHistory(
    agent_executor,
    get_session_history=get_session_history,
    input_messages_key="input",
    history_messages_key="chat_history"
)

# Função principal
def programs_agent(user_input, session_id):
    while True:
        if user_input.lower() in ("sair", "end", "fim", "tchau", "bye"):
            print("Tchau, qualquer dúvida, pode me chamar que eu estarei por aqui!")
            break
        try:
            resposta = chain.invoke(
                {"input": user_input},
                config={"configurable": {"session_id": session_id}}
            )

            output_text = resposta.get("output", "")
            context = resposta.get("chat_history", [])

            return output_text, context
        except Exception as e:
            print("erro ao consumir API: ", e)
            return "", []
        