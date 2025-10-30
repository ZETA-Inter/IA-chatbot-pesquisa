# Importações
from zoneinfo import ZoneInfo
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    HumanMessagePromptTemplate,
    AIMessagePromptTemplate)
from langchain.agents import create_tool_calling_agent , AgentExecutor
from langchain_core.prompts.few_shot import FewShotChatMessagePromptTemplate
from langchain_core.runnables.history import RunnableWithMessageHistory
import os
from dotenv import load_dotenv
from datetime import datetime
from agents.pg_tools import PROGRAMS_TOOLS
from agents.memory_agent import get_memory
import json

# Carrega as envs
load_dotenv()

# timezone
TZ = ZoneInfo("America/Sao_Paulo")
today = datetime.now(TZ).date()

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

agent = create_tool_calling_agent(llm, PROGRAMS_TOOLS, prompt)
agent_executor = AgentExecutor(agent=agent, tools=PROGRAMS_TOOLS, verbose=False)

# Função principal
def programs_agent(user_input, session_id):
    while True:
        memory = get_memory(session_id)
        try:
            resposta = agent_executor.invoke(
                {
                    "input": user_input,
                    "chat_history": memory.messages
                }
            )

            output_text = resposta.get("output", "")
            context = memory.messages

            return output_text, context
        except Exception as e:
            print("erro ao consumir API: ", e)
            return "", []
        