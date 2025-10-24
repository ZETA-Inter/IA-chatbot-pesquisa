# Importações
import uuid
import os
from dotenv import load_dotenv
from langchain_mongodb import MongoDBChatMessageHistory
from agents.search_agent import search_agent
from agents.guardrail import guardrail_agent
from agents.memory_agent import get_memory

# Carrega as envs
load_dotenv()

# Função para executar o fluxo do programs_agent
def run_search(user_input, session_id):
    if not session_id:
        session_id = str(uuid.uuid4())

    # Inicia o histórico no mongodb
    chat_history = get_memory(session_id)

    # Salva a mensagem do usuário
    chat_history.add_user_message(user_input)

    # 1 - Passa pela validação do guardrail
    guardrail_valid, guardrail_message = guardrail_agent(user_input, session_id)
    if not guardrail_valid:
        chat_history.add_ai_message(guardrail_message)
        return guardrail_message, session_id
    
    # 2 - Chama o agente search_agent
    search_output = search_agent(user_input, session_id)
    chat_history.add_ai_message(search_output)

    return search_output, session_id

