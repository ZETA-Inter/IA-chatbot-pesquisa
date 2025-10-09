from programs_pipeline import run_programs_pipeline  # se o arquivo que mostrou se chama pipeline.py
from search_pipeline import run_search_pipeline  # se o arquivo que mostrou se chama pipeline.py
import uuid

# Cria um ID único de sessão (pode ser reaproveitado em conversas futuras)
session_id = str(uuid.uuid4())

# Mensagem de teste
query = "Quais são as boas práticas no transporte de animais?"
query2 = "O que é estresse pré-abate?"
query3 = "O que é a lei 9013/2017?"
query4 = "Qual curso fala sobre abate de bovinos?"
query5 = "Vocês são inuteis, burros!" # testa o guardrail para palavras ofensivas
query6 = "Animais fazem sexo?" # testa o guardrail se palavras obscenas

# Teste com o programs
# response = run_programs_pipeline(query6, str(uuid.uuid4()))

# print("\n=== RESPOSTA FINAL DO PIPELINE PROGRAMS ===")
# print(response)


# teste com o search
response = run_search_pipeline(query4, str(uuid.uuid4()))

print("\n=== RESPOSTA FINAL DO PIPELINE SEARCH ===")
print(response)
