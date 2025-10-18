# Importações
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
from sentence_transformers import SentenceTransformer

# Carrega as envs
load_dotenv()

# Declarando as variáveis do mongo
MONGODB_URL = os.getenv("MONGODB_URL") 
client = MongoClient(MONGODB_URL)
db = client["Zeta"]
classes = db["classes"]
class_embeddings = db["class_embeddings"]

# Conexão com o postgres
POSTGRES_URL = os.getenv("POSTGRES_URL")
conn = psycopg2.connect(POSTGRES_URL)
cur = conn.cursor()

# Embedding
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_MODEL = SentenceTransformer(EMBEDDING_MODEL_NAME)

# Classes das tools de programs
class GetLawArgs(BaseModel):
    law_number: str = Field(..., description="Número da lei (ex: 'Portaria MAPA nº 1234/2020', '9888/2019').")
    topic: Optional[str] = Field(default=None, description="Tópico específico dentro da lei (opcional).")

class GetTopicArgs(BaseModel):
    topic: str = Field(..., description="Tópico ou palavra-chave a buscar.")
    
class GetTopicByLawArgs(BaseModel):
    topic: str =Field(..., description="Tópico ou palavra-chave a buscar no campo 'law.description'.")

# Classes das tools de search
class SearchProgramsArgs(BaseModel):
    topic: str = Field(..., description="Tópico ou palavra-chave a buscar.")


# TOOLS DE PROGRAMS -------------------------------------------------------
# Tool: GetLawArgs
@tool("get_law", args_schema=GetLawArgs)
def get_law(
    law_number: str,
    topic: Optional[str] = None
) -> dict:
    """
    Busca uma lei, portaria ou instrução específica no banco de dados MongoDB pelo número ou identificador completo.
    A busca é flexível para lidar com formatos como 'Portaria MAPA nº 365/2021'.
    Se um tópico for fornecido, retorna informações relacionadas a esse tópico dentro da lei.
    """
    try:
        # Query do MongoDB: utilizando o índice em classes, procura em laws.number o número da lei, decreto ou instrução normativa
        pipeline = [
            {
                "$search": {
                    "index": "idx_classes_search",
                    "text": {
                        "query": law_number,
                        "path": "laws.number"
                    }
                }
            },
            {"$limit": 3},
            {"$project": {"laws": 1, "_id": 0}}
        ]

        # Transforma o resultado em uma lista
        results = list(classes.aggregate(pipeline))

        # Caso esteja vazio o retorno
        if not results:
            return {
                "status": "error",
                "message": f"Nenhuma lei encontrada com o número '{law_number}'."
            }
        
        # Pega o primeiro documento
        laws_obj = results[0].get("laws", [])
        matched_laws = []

        # Adiciona a descrição da lei ao matched_laws
        for law in laws_obj:
            description = law.get("description", "")

            if topic:
                if topic.lower() in description.lower(): 
                    matched_laws.append(law)
            else:
                matched_laws.append(law)

        # Retorna a descrição da lei procurada
        return {
            "status": "ok",
            "results": matched_laws
        }

        
    except Exception as e:
        return {"status": "error", "message": f"Erro na busca utilizando Atlas Search: {str(e)}"}
    
# Tool: GetTopicByLawArgs
@tool("get_topic_by_law", args_schema=GetTopicByLawArgs)
def get_topic_by_law(
    topic: str
) -> dict:
    """
    Busca um tópico ou palavra-chave (utilizando embeddings) no campo 'law.description', na collection 'classes' 
    no banco de dados MongoDB, e retorna o número e a descrição da lei no banco de dados MongoDB.
    """
    try:
        # Query do MongoDB: utilizando o índice de classes, procura um tópico dentro de laws.description para retornar o nº da lei, decreto ou instrução normativa
        pipeline = [
            {
                "$search": {
                    "index": "idx_classes_search",
                    "text": {
                        "query": topic,
                        "path": "laws.description"
                    }
                }
            },
            {"$limit": 5},
            {"$project": {"laws": 1, "_id": 0}}
        ]

        # Transforma o resultado em uma lista
        results = list(classes.aggregate(pipeline))

        # Caso esteja vazio o retorno
        if not results:
            return {
                "status": "error",
                "message": f"Nenhum resultado encontrado para o tópico '{topic}'."
            }
        
        # Caso tenha conteúdo, adiciona as leis ao laws_obj
        laws_obj = []
        for doc in results:
            for law in doc.get("laws", []):
                if law not in laws_obj:
                    laws_obj.append(law)

        # Retorna as leis e o tópico procurado
        return {
            "status": "ok",
            "topic": topic,
            "results": laws_obj
        }

    except Exception as e:
        return {"status": "error", "message": f"Erro na bsuca: {str(e)}"}

# Tool: GetTopicArgs
@tool("get_topic", args_schema=GetTopicArgs)
def get_topic(
    topic: str
) -> dict:
    """
    Busca um tópico ou palavra-chave no banco de dados MongoDB usando a busca vetorial (RAG) para 
    encontrar o conteúdo semanticamente mais relevante nas classes do curso.
    """

    # Verifica se o modelo de embedding existe
    if EMBEDDING_MODEL is None:
        return {"status": "error", "results": [], "message": "Modelo de embedding indisponível. Não é possível fazer a busca RAG."}
        
    try:
        # Gera o embedding da Pergunta do Usuário
        query_vector = EMBEDDING_MODEL.encode(topic).tolist()

        # Recupera todos os documentos com embeddings
        docs = class_embeddings.find({}, {"class_id": 1, "title": 1, "source": 1, "embedding_vector": 1})
        
        # Query do MongoDB: utilizando o índice do Atlas Search Vector na collection class_embeddings, ele pega a o embedding do input do usuário e faz a comparação com os documentos com embedding
        # Ele faz a similaridade dos cossenos e depois escolhe os 5 mais próximos para retornar
        pipeline = [
            {
                "$vectorSearch": {  
                    "index": "idx_vector_embedding",
                    "path": "embedding_vector",
                    "queryVector": query_vector,
                    "numCandidates": 100,   
                    "limit": 5,             
                    "similarity": "cosine"  
                }
            },
            {
                "$project": {
                    "_id": 1,
                    "class_id": 1,
                    "source": 1,
                    "text": 1,
                    "score": {"$meta": "vectorSearchScore"}
                }
            },
            {"$sort": {"score": -1}}
        ]

        # Transforma o retorno em lista
        results = list(class_embeddings.aggregate(pipeline))
        
        # Caso esteja vazio o retorno
        if not results:
            return {"status": "error", "message": f"Nenhum conteúdo encontrado para '{topic}'."}

        # Caso não, ele itera o resultado e adiciona em formatted_results, como tudo formatado com o texto, o campo procurado e o score
        formatted_results = []
        for r in results:
            formatted_results.append({
                "text": r.get("text", ""),
                "source": r.get("source", ""),
                "relevance_score": round(r.get("score", 0), 2)
            })

        # Retorna o tópico do input e a resposta formatada
        return {
            "status": "ok",
            "topic": topic,
            "results": formatted_results
        }

        
    except Exception as e:
        return {"status": "error", "results": [], "message": f"Erro na busca utilizando RAG: {str(e)}"}
    

# TOOLS DE SEARCH -------------------------------------------------------
# Tool: SearchProgramsArgs
@tool("search_programs", args_schema=SearchProgramsArgs)
def search_programs(
    topic: str
) -> dict:
    """
    Busca cursos relacionados a um tópico usando embeddings salvos no MongoDB.
    Retorna os nomes dos cursos.
    """
    
    try:
        # Separa o input do usuário
        query = topic.strip()

        # Query do MongoDB: utilizando o índice em classes, procura a query e retorna o título, o conteúdo e as descrições (tanto da aula quanto da lei)
        # Depois, é retornado o número do curso
        pipeline = [
            {
                "$search": {
                    "index": "idx_classes_search",  # índice de search criado no MongoDB Atlas
                    "text": {
                        "query": query,
                        "path": ["title", "content", "laws.description", "description"]
                    }
                }
            },
            {"$limit": 3},  # Top 3 resultados
            {"$project": {
                "_id": 0,
                "program_id": 1
            }}
        ]

        # Transforma o resultado em lista
        results = list(classes.aggregate(pipeline))

        # Caso esteja vazio o retorno
        if not results:
            return {"status": "error", "message": f"Nenhum conteúdo relevante encontrado para o tópico '{topic}'."}

        # Caso não, extrai os IDs dos programas dos resultados
        program_ids = [res["program_id"] for res in results if res.get("program_id")]

        if not program_ids:
            return {"status": "error", "message": f"Nenhum ID de programa encontrado nos resultados para o tópico '{topic}'."}

        # Monta uma query com os ids extraídos de program_ids
        ids = ', '.join(['%s'] * len(program_ids))
        sql_query = f"SELECT name FROM programs WHERE id IN ({ids})"
        
        # Executa a query montada
        cur.execute(sql_query, tuple(program_ids))
        results = cur.fetchall()

        if not results:
            return {"status": "error", "message": "Nenhum curso encontrado para os IDs retornados."}
        
        # Extrai os nomes dos cursos da tupla de resultados
        programs = [program[0] for program in results]

        # Retorna o tópico e o nome dos cursos correspondentes
        return {
            "status": "ok",
            "query": topic,
            "programs": programs
        }
    
    except Exception as e:
        return {"status": "error", "message": f"Erro na busca utilizando embedding no MongoDB: {str(e)}"}

# Exporta a lista de tools
PROGRAMS_TOOLS = [get_law, get_topic, get_topic_by_law]

SEARCH_TOOLS = [search_programs]