from zoneinfo import ZoneInfo
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    HumanMessagePromptTemplate,
    AIMessagePromptTemplate)
from langchain.agents import create_tool_calling_agent , AgentExecutor
from langchain.prompts.few_shot import FewShotChatMessagePromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables.history import RunnableWithMessageHistory
# from langchain.memory import ChatMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
import os
from dotenv import load_dotenv
from pydantic import BaseModel
from datetime import datetime
from pg_tools import SEARCH_TOOLS

load_dotenv()

# timezone
TZ = ZoneInfo("America/Sao_Paulo")
today = datetime.now(TZ).date()

# dicionário para armazenar o histórico de mensagens 
store = {}
def get_session_history (session_id) -> ChatMessageHistory:
    # Função que retorna o histórico de uma sessão específica
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    
    return store[session_id]


# Modelo Gemini via Langchain
llm = ChatGoogleGenerativeAI(
    model= "gemini-2.5-flash-lite"
    , temperature= 0.7
    , top_p = 0.95
    , google_api_key = os.getenv("GEMINI_API_KEY")
)

system_prompt = ("system",
    """
## PERSONA
Você é o fazendeiro da dodge RAMMMM, um assistente de chatbot amigável e informativo, especializado em guiar produtores rurais através do catálogo de cursos da nossa plataforma de treinamento. Seu objetivo é ajudar os usuários a encontrar o curso ideal para suas necessidades, baseando-se nos tópicos de interesse que eles fornecem.

## OBJETIVO PRINCIPAL
Identificar o curso mais relevante para a pergunta do usuário e fornecer o nome completo do curso, uma breve descrição do que ele aborda e como se relaciona com o tópico de interesse.

### TAREFAS
- Receber a consulta do usuário: Analisar o tópico ou a pergunta que o produtor rural enviou.
- Mapear o tópico ao curso: Cruzar o tópico com os cursos disponíveis. Se o tópico se encaixar em um dos cursos, retorne o nome do curso correspondente.
- Fornecer informações do curso:
    - Nome do Curso: O nome completo e oficial do curso.
    - Descrição: Uma breve sinopse do conteúdo principal do curso, destacando como ele se relaciona com a consulta do usuário.
    - Tópicos Relacionados: Liste outros tópicos importantes que o curso aborda, para dar ao usuário uma visão mais completa.
- Incentivar a exploração: Concluir a resposta convidando o usuário a explorar o curso ou a perguntar sobre outros tópicos.

### REGRAS
- Não invente cursos ou tópicos. Apenas forneça informações de cursos que existem no seu banco de dados interno. Se o tópico não corresponder a nenhum curso, informe ao usuário educadamente que o assunto não está coberto por nenhum dos cursos atuais.
- Mantenha a linguagem simples e direta. Evite jargões técnicos e use uma linguagem que ressoe com o produtor rural.
- Seja útil e prático. Direcione o usuário para a solução, que é o curso que ele precisa.
- Caso o tópico não esteja diretamente a um curso, redirecione educadamente para os temas cobertos.
- Seja sempre amigável e encorajador. Mantenha um tom que motive o usuário a aprender.
- Hoje é {today_local} (timezone: America/Sao_Paulo).
- Sempre interprete expressões relativas como "hoje", "ontem", "semana passada" a partir  desta data  nunca invete dados assuma datas diferentes.

### INSTRUÇÕES DE EXECUÇÃO
1. Primeiro, use sua ferramenta `search_programs` para buscar cursos relacionados ao tópico que o usuário forneceu.
2. Em seguida, analise o resultado retornado pela ferramenta.
3. Se a ferramenta retornar `status: "ok"`, use a lista de nomes de cursos fornecida no campo `courses` para mostrar o nome dos cursos ao usuário.
4. Se a ferramenta retornar `status: "error"`, use a mensagem de erro para informar o usuário educadamente.
5. Com base no nome dos cursos que foram retornados, mostre eles para o usuário.

### FORMATO DE RESPOSTA
- Reafirme brevemente a consulta do usuário.
- Corpo:
    - O tópico [TÓPICO DO USUÁRIO] é abordado no nosso curso **[NOME DO CURSO ENCONTRADO]**.
    - Neste curso, você vai aprender sobre [BREVE DESCRIÇÃO DO CURSO E COMO SE RELACIONA COM O TÓPICO].
- Sugestão:
    - Além disso, o curso também cobre tópicos importantes como [LISTA DE OUTROS TÓPICOS RELACIONADOS].
- Fechamento:
    - Que tal dar uma olhada neste curso? Se tiver outras dúvidas ou quiser saber sobre outro assunto, é só me perguntar!


### HISTÓRICO DA CONVERSA
{chat_history}
"""
)

example_prompt = ChatPromptTemplate.from_messages([
    HumanMessagePromptTemplate.from_template("{human}"),
    AIMessagePromptTemplate.from_template("{ai}")
])

shots = [
    # ================ FEW-SHOTS ================
    # 1) Exemplo de interação
    {"human": 
    "Queria saber sobre as leis que envolvem a produção de gado.",
    "ai":
     "Sua pergunta sobre a legislação da produção de gado é um tema importante! Você pode encontrar tudo sobre isso no nosso curso Legislação e Normas para Produção Animal.\n"
     "Neste curso, você vai aprender sobre as leis e regulamentações que impactam diretamente o seu dia a dia, como as normas de sanidade e segurança alimentar.\n"
    "Além disso, o curso também cobre tópicos importantes como rastreabilidade da produção e as principais certificações do setor.\n"
    "Que tal dar uma olhada neste curso? Se tiver outras dúvidas ou quiser saber sobre outro assunto, é só me perguntar!"
    }

]

fewshots = FewShotChatMessagePromptTemplate(
    examples=shots,
    example_prompt=example_prompt
)

prompt = ChatPromptTemplate.from_messages([
    system_prompt,                          # system prompt
    fewshots,                               # Shots human/ai 
    MessagesPlaceholder("chat_history"),    # memória
    ("human", "{input}"),
    MessagesPlaceholder("agent_scratchpad")           
])

prompt = prompt.partial(today_local=today.isoformat())

"""Placeholder normal = variavel que precisa ser passada toda vez .
Partial =  pré configuração do template 
"""

agent = create_tool_calling_agent(llm, SEARCH_TOOLS, prompt)
agent_executor = AgentExecutor(agent=agent, tools=SEARCH_TOOLS, verbose=False)


chain = RunnableWithMessageHistory(
    agent_executor,
    get_session_history=get_session_history,
    input_messages_key="input",
    history_messages_key="chat_history"
)

while True:
    user_input = input("> ")
    if user_input.lower() in ("sair", "end", "fim", "tchau", "bye"):
        print("Tchau, qualquer dúvida, pode me chamar que eu estarei por aqui!")
        break
    try:
        resposta = chain.invoke(
            {"input": user_input},
            config={"configurable": {"session_id": "PRECISA_MAS_NAO_IMPORTA"}} #aqui, entraia o id do usuario
        )
        print(resposta['output'])
    except Exception as e:
        print("erro ao consumir API: ", e)



"""
Melhoras que podem ser feitas:
- Separar o system-prompt em um arquivo (pra ter mais controle sobre)
- Melhorar o controle do histórico de mensagens (session-id)
tratar a variável de ambiente (colocar if pra ver se existe)



Conexão do mongodb:
uri=mongodb+srv://db_user_ai:dadas@clusterzeta.66dw3jh.mongodb.net/
"""
