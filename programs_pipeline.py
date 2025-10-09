import uuid
import os
from dotenv import load_dotenv
from langchain_mongodb import MongoDBChatMessageHistory
from agents.programs_agent import programs_agent
from agents.guardrail import guardrail_agent
from agents.judge import judge_agent

# Carrega as envs
load_dotenv()

# Função para executar o fluxo do programs_agent
def run_programs(user_input, session_id):
    if not session_id:
        session_id = str(uuid.uuid4())

    # Inicia o histórico no mongodb
    chat_history = MongoDBChatMessageHistory(
        session_id=session_id,
        connection_string=os.getenv("MONGODB_URL")
    )

    # Salva a mensagem do usuário
    chat_history.add_user_message(user_input)

    # 1 - Passa pela validação do guardrail
    guardrail_valid, guardrail_message = guardrail_agent(user_input, session_id)
    if not guardrail_valid:
        chat_history.add_ai_message(guardrail_message)
        return guardrail_message
    
    # 2 - Chama o agente programs_agent
    programs_output, programs_context = programs_agent(user_input, session_id)

    # 3 - Chama o juiz
    judge_valid, judge_evaluation = judge_agent(user_input, programs_output, programs_context, session_id)
    if judge_valid:
        chat_history.add_ai_message(programs_output)
        return programs_output
    else:
        chat_history.add_ai_message(judge_evaluation)
        return judge_evaluation


if __name__ == "__main__":
    print("Início da conversa---------------------")
    session_id = str(uuid.uuid4())

    user_input = "Qual a lei que fala sobre inspeção sanitária e industrial?"
    result = run_programs(user_input, session_id)
    print(result)



# Testes ------------------------
"""
O que é a lei 7889/1989? (deve falar da lei)
O que é a lei 9013/2017? (deve falar que é um decreto e depois falar o que é)
O que é manejo calmo? (explica o que é e as causas)
Qual a lei que fala sobre inspeção sanitária e industrial? (fala das leis 9013/2017 e ciota sobre o decreto 7889/1989)


# Mensagem de teste
query = "Quais são as boas práticas no transporte de animais?"
query2 = "O que é estresse pré-abate?"
query3 = "O que é a lei 9013/2017?"
query4 = "Qual curso fala sobre abate de bovinos?"
query5 = "Vocês são inuteis, burros!" # testa o guardrail para palavras ofensivas
query6 = "Animais fazem sexo?" # testa o guardrail se palavras obscenas





"""


    
    