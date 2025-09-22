import os
from dotenv import load_dotenv
import psycopg2
from typing import Optional
from langchain.tools import tool
from pydantic import BaseModel, Field
from datetime import datetime
from zoneinfo import ZoneInfo
from pymongo import MongoClient
import psycopg2


load_dotenv()

# Declarando as variáveis do mongo
MONGODB_URL = os.getenv("MONGODB_URL") 
client = MongoClient(MONGODB_URL)
db = client["Zeta"]
classes = db["classes"]
activities = db["activities"]
counter = db["counter"]

# Conexão com o postgres
POSTGRES_URL = os.getenv("POSTGRES_URL")
conn = psycopg2.connect(POSTGRES_URL)
cur = conn.cursor()

# Teste de conexão
# cur.execute("SELECT * from programs")
# print(cur.fetchall())

# Declarando as variáveis do postgres

# teste da conexão
# print(MONGODB_URL)
# print(db.list_collection_names())

# Classes das tools de programs
class GetLawArgs(BaseModel):
    law_number: int = Field(..., description="Número da lei (ex: 1234/2020, 9888).")
    topic: Optional[str] = Field(default=None, description="Tópico específico dentro da lei (opcional).")

class GetTopicArgs(BaseModel):
    topic: str = Field(..., description="Tópico ou palavra-chave a buscar.")
    
# Classes das tools de search
class SearchProgramsArgs(BaseModel):
    topic: str = Field(..., description="Tópico ou palavra-chave a buscar.")

# TOOLS DE PROGRAMS
# Tool: GetLawArgs
@tool("get_law", args_schema=GetLawArgs)
def get_law(
    law_number: int,
    topic: Optional[str] = None
) -> dict:
    """
    Busca uma lei específica no banco de dados MongoDB.
    Se um tópico for fornecido, retorna informações relacionadas a esse tópico dentro da lei.
    """
    try:
        query = {"laws.number": law_number}
        projection = {"_id": 0, "laws.$": 1}  # pega apenas a lei correspondente

        law_doc = classes.find_one(query, projection)

        if law_doc is None:
            return {"status": "error", "message": "Lei não encontrada."}

        law_obj = law_doc["laws"][0]

        if topic:
            if topic.lower() in law_obj["description"].lower():
                return {"status": "ok", "law": law_obj, "topic_found": True}
            else:
                return {"status": "error", "message": f"Tópico '{topic}' não encontrado na lei."}

        return {"status": "ok", "law": law_obj}

    except Exception as e:
        return {"status": "error", "message": str(e)}

# Tool: GetTopicArgs
@tool("get_topic", args_schema=GetTopicArgs)
def get_topic(
    topic: str
) -> dict:
    """
    Busca um tópico ou palavra-chave no banco de dados MongoDB.
    Pode filtrar por ID de aula ou atividade se fornecido.
    """
    try:
        query = {"$text": {"$search": topic}}

        projection = {"_id": 0, "text": 1, "program_id": 1}

        result_classes = classes.find(query, projection)
        result_activities = activities.find(query, projection)

        if not result_classes and not result_activities:
            return {"status": "error", "message": "Nenhum resultado encontrado para o tópico fornecido."}
        if not result_classes:
            results = list(result_activities)
        elif not result_activities:
            results = list(result_classes)
        else:
            results = list(result_classes) + list(result_activities)

        return {"status": "ok", "results": results}

    except Exception as e:
        return {"status": "error", "message": str(e)}


# TOOLS DE SEARCH
@tool("search_programs", args_schema=SearchProgramsArgs)
def search_programs(
    topic: str
) -> dict:
    """
    Busca cursos relacionados a um tópico ou palavra-chave.
    """
    program_ids = []
    program_names = []

    try:
        query = {"$text": {"$search": topic}}
        projection = {"_id": 0, "program_id": 1}

        result_ids = classes.find(query, projection)
        print(result_ids)

        for doc in result_ids:
            program_ids.append(doc["program_id"])

        if not program_ids:
            return {"status": "error", "message": "Nenhum curso encontrado para o tópico fornecido."}
        
        # Constrói a consulta SQL de forma segura usando placeholders
        ids = ', '.join(['%s'] * len(program_ids))
        sql_query = f"SELECT name FROM programs WHERE id IN ({ids})"
        
        cur.execute(sql_query, tuple(program_ids))
        
        # Obtém todos os resultados
        results = cur.fetchall()
        
        # Extrai os nomes dos cursos da tupla de resultados
        courses = [course[0] for course in results]

        return {"status": "ok", "courses": courses}

    except Exception as e:
        return {"status": "error", "message": str(e)}



# Exporta a lista de tools
PROGRAMS_TOOLS = [get_law, get_topic]

SEARCH_TOOLS = [search_programs]



""" 
Estrutura do mongo:
Classes
- program_id
- ⁠images [array]
- ⁠text
- ⁠flashcards [array]
- ⁠laws [array]
Activities
- class_id
- images [array]
- ⁠points 
- ⁠question
- ⁠answer


tools para o chatbot do curso:
- procurar sobre alguma lei
- procurar sobre algum tópico do curso
- procurar ak=lgum termo específico





"""