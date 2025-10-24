# Importações
import uuid
import os
from dotenv import load_dotenv
from langchain_mongodb import MongoDBChatMessageHistory
from agents.programs_agent import programs_agent
from agents.guardrail import guardrail_agent
from agents.judge import judge_agent
from agents.memory_agent import get_memory

# Carrega as envs
load_dotenv()

# Função para executar o fluxo do programs_agent
def run_programs(user_input, session_id):
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
    
    # 2 - Chama o agente programs_agent
    programs_output, programs_context = programs_agent(user_input, session_id)

    # 3 - Chama o juiz
    judge_valid, judge_evaluation = judge_agent(user_input, programs_output, programs_context, session_id)
    if judge_valid:
        chat_history.add_ai_message(programs_output)
        return programs_output, session_id
    else:
        chat_history.add_ai_message(judge_evaluation)
        return judge_evaluation, session_id
