import os
from dotenv import load_dotenv
import uuid
from langchain_mongodb import MongoDBChatMessageHistory
from agents.guardrail import guardrail_agent
from agents.judge import judge_agent
from agents.programs_agent import programs_agent

load_dotenv()
MONGODB_URL = os.getenv("MONGODB_URL")

def run_search_pipeline(query, session_id):
    if session_id is None:
        session_id = str(uuid.uuid4())

    # Inicializa o histórico do MongoDB para essa sessão
    chat_message_history = MongoDBChatMessageHistory(
        session_id=session_id,
        connection_string=MONGODB_URL,
        database_name="Zeta",
        collection_name="conversations_log",
    )

    # Salva a mensagem do usuário
    chat_message_history.add_user_message(query)

    # Etapa 1 - Se o guardrail considerar a query inadequada, retorna uma resposta negativa
    guard_is_valid, guard_output = guardrail_agent(query, session_id)
    if not guard_is_valid:
        chat_message_history.add_ai_message(guard_output)
        return guard_output
    
    # Etapa 2 - Recupera contexto e gera resposta (RAG)
    program_output, program_context = programs_agent(query, session_id)

    # Etapa 3 - Se o juiz aprova, a resposta original é enviada. Se rejeita, retorna a resposta ajustada
    judge_is_valid, judge_output = judge_agent(query, program_output, program_context, session_id)
    if judge_is_valid:
        chat_message_history.add_ai_message(program_output)
        return program_output
    else:
        chat_message_history.add_ai_message(judge_output)
        return judge_output
