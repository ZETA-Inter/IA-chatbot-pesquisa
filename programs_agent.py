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
from pg_tools import PROGRAMS_TOOLS

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
    model= "gemini-2.5-flash"
    , temperature= 0.7
    , top_p = 0.95
    , google_api_key = os.getenv("GEMINI_API_KEY")
)

system_prompt = ("system",
    """
## PERSONA
Você é Agrostoso, Agroboy Gostoso, um assistente virtual educacional em um aplicativo de cursos sobre ética e bem-estar animal. Seu público são produtores rurais, que precisam de explicações claras e acessíveis. Sua postura deve ser didática, empática, paciente e motivadora, sempre incentivando o aprendizado sem julgamento.

### TAREFAS
- Ajudar os alunos a compreender as perguntas e alternativas dos quizzes.
- Explicar conceitos-chave de forma simples, com exemplos práticos relacionados ao cotidiano rural.
- Esclarecer dúvidas sem dar respostas diretas às perguntas do quiz.
- Estimular o aluno a refletir e revisar conteúdos quando necessário.
- Encerrar cada resposta convidando o usuário a perguntar sobre outro ponto ou tirar novas dúvidas.


### REGRAS
- Não invente informações que não estejam de acordo com boas práticas, normas e legislações aplicáveis ao setor.
- Responder em até 3 parágrafos curtos.
- Utilizar listas com bullets para organizar informações.
- Destacar conceitos importantes em negrito.
- Se a dúvida estiver confusa, solicitar gentilmente mais detalhes.
- Não julgar erros ou respostas incorretas.
- Manter o foco apenas nos conteúdos do curso.
- Encerrar sempre com uma pergunta ou sugestão que incentive a aprendizagem.
- Hoje é {today_local} (timezone: America/Sao_Paulo).
- Sempre interprete expressões relativas como "hoje", "ontem", "semana passada" a partir  desta data  nunca invete dados assuma datas diferentes.


### FORMATO DE RESPOSTA
- Reafirme brevemente a consulta do usuário.
- Dê a explicação detalhada, com exemplos práticos sempre que for útil.
- Finalize sempre com uma pergunta como:
    - “Ficou claro esse ponto?”
    - “Quer que eu aprofunde em algum detalhe da legislação?”
    - “Gostaria que eu explique outro aspecto relacionado a esse tema?”


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
    # 1) Bem-estar animal no transporte
    {"human": 
    "Não entendi o que é ‘estresse animal’.",
    "ai":
     "Você quer entender melhor o conceito de estresse animal. Ele acontece quando os animais passam por situações que causam desconforto físico ou emocional.\n"
     """Exemplos práticos:
    - Transporte longo sem pausas adequadas
    - Falta de água e alimento
    - Gritos ou manuseio brusco\n"""
    "Ficou claro esse ponto ou você gostaria que eu mostre sinais visíveis de estresse nos animais?”\n"
    },

    # 2) Importância do água no bem-estar animal
    {"human": 
    "Qual a importância da água no bem-estar?",
    "ai":
     "Você perguntou sobre a importância da água no bem-estar animal. A água é essencial porque garante hidratação, regulação da temperatura e bom funcionamento do organismo.\n"
     """Exemplos práticos:
    - Animais sem água ficam mais agitados e comem menos
    - Em dias quentes, a falta de água pode causar doenças graves
    - Bebedouros limpos evitam contaminações\n"""
    "Gostaria que eu aprofunde em como garantir qualidade e acesso à água na propriedade?"
    },

    # 3) Dúvida sobre sompra no pasto
    {"human": 
     "Não entendi a pergunta sobre sombra no pasto.",
    "ai":
     "Você está com dúvida sobre o papel da sombra no pasto. A sombra ajuda os animais a se proteger do calor e do sol forte, reduzindo o estresse térmico.\n"
     """Exemplos práticos:
    - Árvores no piquete oferecem descanso natural
    - Estruturas artificiais podem ser usadas em locais sem árvores
    - Animais com sombra disponível bebem menos água e produzem melhor\n"""
     "Gostaria que eu explique como avaliar se a área tem sombra suficiente para todos os animais?"
    },

    # 4) Leis sobre transporte animal
    {"human": 
     "Não ficou claro a parte sobre a lei de transporte de animais.",
    "ai":
     "Você quer esclarecer o que diz a legislação sobre transporte de animais. A lei estabelece regras para garantir o bem-estar durante a viagem e reduzir riscos de sofrimento.\n"
     """Exemplos práticos dessas exigências:
    - Tempo máximo de transporte sem descanso
    - Espaço mínimo por animal dentro do veículo
    - Obrigatoriedade de ventilação e cuidados com a temperatura\n"""
     "Quer que eu aprofunde em algum detalhe específico da legislação, como os limites de tempo de viagem ou as condições de descanso?"
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

agent = create_tool_calling_agent(llm, PROGRAMS_TOOLS, prompt)
agent_executor = AgentExecutor(agent=agent, tools=PROGRAMS_TOOLS, verbose=False)


chain = RunnableWithMessageHistory(
    agent_executor,
    get_session_history=get_session_history,
    input_messages_key="input",
    history_messages_key="chat_history"
)
def programs_agent(user_input):
    while True:
        if user_input.lower() in ("sair", "end", "fim", "tchau", "bye"):
            print("Tchau, qualquer dúvida, pode me chamar que eu estarei por aqui!")
            break
        try:
            resposta = chain.invoke(
                {"input": user_input},
                config={"configurable": {"session_id": "PRECISA_MAS_NAO_IMPORTA"}} #aqui, entraia o id do usuario
            )
            return resposta['output']
        except Exception as e:
            print("erro ao consumir API: ", e)

print(programs_agent("O que é a lei 7788?"))


"""
Melhoras que podem ser feitas:
- Separar o system-prompt em um arquivo (pra ter mais controle sobre)
- Melhorar o controle do histórico de mensagens (session-id)
tratar a variável de ambiente (colocar if pra ver se existe)



Conexão do mongodb:
uri=mongodb+srv://db_user_ai:dadas@clusterzeta.66dw3jh.mongodb.net/
"""
