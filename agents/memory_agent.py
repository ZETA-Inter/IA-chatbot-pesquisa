# Importações
import os
from dotenv import load_dotenv
from langchain_mongodb import MongoDBChatMessageHistory

# Carrega as envs
load_dotenv()

# Atribui a uma variável a env do banco do MongoDB
MONGODB_URL = os.getenv("MONGODB_URL") 

# Função para criar um log das conversas
def get_memory(session_id):

    # Se a chave estiver vazia
    if not MONGODB_URL:
        print("A variável MONGODB_URL naõ está definida.")

    # Se não, cria um documento no MongoDB de log da conversa
    return MongoDBChatMessageHistory(
        session_id=session_id,
        connection_string=MONGODB_URL,
        database_name="Zeta",
        collection_name="conversations_log",
    )