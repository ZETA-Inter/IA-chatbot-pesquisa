import uuid
import os
from dotenv import load_dotenv
from langchain_mongodb import MongoDBChatMessageHistory
from agents.search_agent import search_agent
from agents.guardrail import guardrail_agent
from agents.judge import judge_agent

# Carrega as envs
load_dotenv()

# Função para executar o fluxo do programs_agent
def run_search(user_input, session_id):
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
    
    # 2 - Chama o agente search_agent
    search_output, search_context = search_agent(user_input, session_id)

    return search_output


if __name__ == "__main__":
    print("Início da conversa---------------------")
    session_id = str(uuid.uuid4())

    user_input = "Qual é a idade ideal para o abate de animais?"
    result = run_search(user_input, session_id)
    print(result)



# Testes ------------------------
"""
Tem algum curso sobre bem-estar animal?
Qual cursos vocês têm sobre normas para os animais?
Qual curso fala sobre a alimentação dos bois?

# Mensagem de teste
query = "Quais são as boas práticas no transporte de animais?"
query2 = "O que é estresse pré-abate?"
query3 = "O que é a lei 9013/2017?"
query4 = "Qual curso fala sobre abate de bovinos?"
query5 = "Vocês são inuteis, burros!" # testa o guardrail para palavras ofensivas
query6 = "Animais fazem sexo?" # testa o guardrail se palavras obscenas





"""


    
    