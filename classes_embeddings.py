# Importações
from pymongo import MongoClient
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
from dotenv import load_dotenv
import google.generativeai as genai
import datetime

# Carrega as envs
load_dotenv()

# Declarando as variáveis do mongo
MONGODB_URL = os.getenv("MONGODB_URL")
client = MongoClient(MONGODB_URL)
db = client["Zeta"]
classes = db["classes"]
class_embeddings = db["class_embeddings"]

# Configuração do Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Splitter para textos grandes
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)

def create_embedding_for_new_class(class_id):
    """
    Função para ser chamada quando um novo documento é inserido manualmente.
    Pode ser usada em seus endpoints da API ou scripts de inserção.
    Args:
        class_id: O _id do documento inserido na collection 'classes'
        
    Returns:
        dict: Status da operação
    """
    try:
        # Busca o documento
        doc = classes.find_one({"_id": class_id})
        
        if not doc:
            return {
                "status": "error",
                "message": f"Documento com ID {class_id} não encontrado"
            }
        
        # Verifica se já existe embedding
        existing_count = class_embeddings.count_documents({"class_id": class_id})
        if existing_count > 0:
            return {
                "status": "warning",
                "message": f"Documento {class_id} já possui {existing_count} embeddings"
            }
        
        docs_to_embed = []

        # Embedding: content
        for text in doc.get("content", []):
            if text:
                chunks = splitter.split_text(text)
                for chunk in chunks:
                    docs_to_embed.append({
                        "source": "content",
                        "text": chunk
                    })

        # Embedding: laws.description
        for law in doc.get("laws", []):
            if "description" in law and law["description"]:
                chunks = splitter.split_text(law["description"])
                for chunk in chunks:
                    docs_to_embed.append({
                        "source": "laws",
                        "law_number": law.get("number"),
                        "text": chunk
                    })

        # Embedding: description
        if doc.get("description"):
            text_to_embed = doc["description"] 
            chunks = splitter.split_text(text_to_embed)

            for chunk in chunks:
                docs_to_embed.append({
                    "source": "description",
                    "text": chunk
                })

        # Gerar embeddings usando Gemini
        embeddings_created = 0
        errors = []
        
        for doc_chunk in docs_to_embed:
            try:
                result = genai.embed_content(
                    model="text-embedding-004",
                    content=doc_chunk["text"],
                    task_type="retrieval_document"
                )
                vector = result['embedding']
                
                doc_chunk["embedding_vector"] = vector
                doc_chunk["class_id"] = class_id
                doc_chunk["created_at"] = datetime.utcnow()

                # Salva na collection de embeddings
                class_embeddings.insert_one(doc_chunk)
                embeddings_created += 1
                
            except Exception as e:
                errors.append(str(e))
                continue

        return {
            "status": "success",
            "class_id": class_id,
            "embeddings_created": embeddings_created,
            "errors": errors if errors else None
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Erro ao processar documento: {str(e)}"
        }

if __name__ == "__main__":
    print("Iniciando geração de embeddings para todas as classes...")

    total_docs = classes.count_documents({})
    print(f"Total de documentos encontrados: {total_docs}")

    processed = 0
    success = 0
    skipped = 0
    errors = []

    for doc in classes.find():
        class_id = doc["_id"]

        # Pula se já existir embedding dessa classe
        existing = class_embeddings.count_documents({"class_id": class_id})
        if existing > 0:
            print(f"Pulando classe {class_id} ({existing} embeddings já existentes).")
            skipped += 1
            continue

        result = create_embedding_for_new_class(class_id)
        processed += 1

        if result["status"] == "success":
            success += 1
            print(f"Classe {class_id} processada com sucesso: {result['embeddings_created']} embeddings criados.")
        else:
            print(f"⚠️ Erro na classe {class_id}: {result.get('message', 'Erro desconhecido')}")
            errors.append({
                "class_id": class_id,
                "error": result.get("message", "Sem mensagem de erro")
            })

    print("\nResumo final:")
    print(f"- Total de classes: {total_docs}")
    print(f"- Processadas agora: {processed}")
    print(f"- Puladas (já possuíam embeddings): {skipped}")
    print(f"- Sucesso: {success}")
    print(f"- Falhas: {len(errors)}")

    if errors:
        print("\nDetalhes dos erros:")
        for err in errors:
            print(f" • Classe {err['class_id']}: {err['error']}")










# # Função para criar o embedding dos campos
# def insert_embeddings():
#     for c in classes.find():
#         class_id = c["_id"]

#         docs_to_embed = []

#         # Embedding: content
#         for text in c.get("content", []):
#             if text:
#                 chunks = splitter.split_text(text)
#                 for chunk in chunks:
#                     docs_to_embed.append({
#                         "source": "content",
#                         "text": chunk
#                     })

#         # Embedding: laws.description
#         for law in c.get("laws", []):
#             if "description" in law and law["description"]:
#                 chunks = splitter.split_text(law["description"])
#                 for chunk in chunks:
#                     docs_to_embed.append({
#                         "source": "laws",
#                         "law_number": law.get("number"),
#                         "text": chunk
#                     })

#         # Embedding: description
#         text_to_embed = c["description"] 
#         chunks = splitter.split_text(text_to_embed)

#         # Cria os chunks   
#         for chunk in chunks:
#             docs_to_embed.append({
#                 "source": "description", # Fonte para identificar o dado na busca
#                 "text": chunk
#             })

#         # gerar embeddings e atualizar no Mongo
#         for doc in docs_to_embed:
#             vector = embedding_model.encode(doc["text"]).tolist()
#             doc["embedding_vector"] = vector
#             doc["class_id"] = class_id

#             # salva em uma nova collection (ex: db["class_embeddings"])
#             db["class_embeddings"].insert_one(doc)

# insert_embeddings()
# print("Embeddings gerados e armazenados!")
