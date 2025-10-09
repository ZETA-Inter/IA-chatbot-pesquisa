import os
from dotenv import load_dotenv
from langchain_mongodb import MongoDBChatMessageHistory
from langchain.memory import ConversationBufferMemory

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL") 

def get_memory(session_id):
    if not MONGODB_URL:
        print("A variável MONGODB_URL naõ está definida.")


    return MongoDBChatMessageHistory(
        session_id=session_id,
        connection_string=MONGODB_URL,
        database_name="Zeta",
        collection_name="conversations_log",
    )