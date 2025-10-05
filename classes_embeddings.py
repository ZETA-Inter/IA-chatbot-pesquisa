from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL")
client = MongoClient(MONGODB_URL)
db = client["Zeta"]
classes = db["classes"]

# Modelo
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# Splitter para textos grandes
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)

def insert_embeddings():
    for c in classes.find():
        class_id = c["_id"]

        docs_to_embed = []

        # content.text
        for item in c.get("content", []):
            if "text" in item and item["text"]:
                chunks = splitter.split_text(item["text"])
                for chunk in chunks:
                    docs_to_embed.append({"source": "content", "text": chunk})

        # laws.description
        for law in c.get("laws", []):
            if "description" in law and law["description"]:
                chunks = splitter.split_text(law["description"])
                for chunk in chunks:
                    docs_to_embed.append({
                        "source": "laws",
                        "law_number": law.get("number"),
                        "text": chunk
                    })

        # description
        text_to_embed = c["description"] 
        chunks = splitter.split_text(text_to_embed)
            
        for chunk in chunks:
            docs_to_embed.append({
                "source": "description", # Fonte para identificar o dado na busca
                "text": chunk
            })
       

        # gerar embeddings e atualizar no Mongo
        for doc in docs_to_embed:
            vector = embedding_model.encode(doc["text"]).tolist()
            doc["embedding_vector"] = vector
            doc["class_id"] = class_id

            # salva em uma nova collection (ex: db["class_embeddings"])
            db["class_embeddings"].insert_one(doc)

            # 🔹 ou salva direto na mesma collection
            # classes.update_one(
            #     {"_id": class_id},
            #     {"$push": {"embedded_texts": doc}}
            # )

insert_embeddings()
print("Embeddings gerados e armazenados!")
