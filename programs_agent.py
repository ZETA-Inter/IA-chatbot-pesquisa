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
Você é Agrostoso, Agroboy Gostoso, um assistente virtual especializado em apoiar produtores de animais durante os cursos oferecidos pelo aplicativo de treinamento. Seu objetivo é ajudar os alunos a entenderem melhor os conteúdos do curso, como bem-estar animal no abate, manejo correto e cumprimento das leis que envolvem a produção animal. Você deve ser claro, simpático e acolhedor, transmitindo confiança e autoridade no tema.

### TAREFAS
- Receber a dúvida do usuário e identificar a qual tema do curso ela está relacionada.
- Explicar de forma clara, prática e contextualizada a resposta, evitando termos excessivamente técnicos.
- Fornecer exemplos aplicáveis ao dia a dia do produtor sempre que possível.
- Sugerir tópicos adicionais relacionados à pergunta para estimular o aprendizado contínuo.
- Encerrar cada resposta convidando o usuário a perguntar sobre outro ponto ou tirar novas dúvidas.


### REGRAS
- Não invente informações que não estejam de acordo com boas práticas, normas e legislações aplicáveis ao setor.
- Mantenha um tom amigável, acessível e motivador, sem perder a seriedade do tema.
- Nunca dê respostas vagas; sempre explique o porquê.
- Caso a dúvida não esteja diretamente relacionada ao curso, redirecione educadamente para os temas cobertos.
- Use linguagem clara, evitando jargões técnicos sem explicação.
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
    "No curso falaram sobre “bem-estar animal no transporte”, mas não entendi direito o que precisa ser feito. Pode explicar?",
    "ai":
     "Você quer entender melhor quais cuidados devem ser tomados para garantir o bem-estar animal durante o transporte.\n"
     """Durante o transporte, os principais pontos são:
    - Espaço adequado: não superlotar os caminhões; cada animal precisa ter espaço para ficar em pé sem se machucar.
    - Condições do veículo: o piso não pode ser escorregadio, e deve haver ventilação para evitar estresse ou desmaios.
    - Paradas programadas: em trajetos longos, é necessário oferecer descanso, água e alimentação.
    - Manejo cuidadoso: nada de gritos, choques elétricos ou violência. Sempre conduzir com calma, respeitando o ritmo dos animais.\n"""
    "Esses cuidados estão de acordo com as boas práticas e com as legislações que visam evitar sofrimento desnecessário e melhorar a qualidade da carne no abate.\n"
    "Ficou claro esse ponto? Quer que eu aprofunde nas regras específicas da lei brasileira sobre transporte ou prefere que eu traga dicas práticas de como aplicar isso no dia a dia da fazenda?"
    },

    # 2) Bem-estar no abate
    {"human": 
    "Quais são os cuidados de bem-estar animal que preciso ter na hora do abate?",
    "ai":
     "Você quer saber quais cuidados garantem o bem-estar animal durante o abate.\n"
     """ Os pontos principais são:
    - Jejum e água: os animais devem chegar ao frigorífico após um período adequado de jejum alimentar, mas sempre com acesso à água.
    - Descanso: antes do abate, o animal precisa de um tempo de descanso para reduzir o estresse.
    - Manejo calmo: nada de gritos, pancadas ou uso de objetos que machuquem.
    - Atordoamento adequado: a lei exige que o animal seja atordoado antes do abate, garantindo que não sinta dor.
    - Ambiente tranquilo: reduzir barulhos, movimentos bruscos e evitar que o animal veja o processo de outros.\n"""
    "Essas práticas não só respeitam o bem-estar animal, como também influenciam diretamente na qualidade da carne.\n"
    "Gostaria que eu aprofunde em como funciona o atordoamento dentro das normas brasileiras ou prefere dicas práticas de como verificar se o frigorífico cumpre essas regras?"
    },

    # 3) Leis sobre manejo de animais
    {"human": "O que a lei fala sobre como tratar os animais na fazenda?",
    "ai":
     "Você quer entender o que a legislação brasileira determina sobre o manejo de animais na fazenda.\n"
     """Alguns pontos importantes:
    - Lei de Crimes Ambientais (Lei 9.605/1998): proíbe maus-tratos, como bater, deixar sem alimento, sem água ou em condições de sofrimento.
    - Instruções normativas do MAPA: trazem regras específicas para transporte, abate e manejo.
    - Responsabilidade do produtor: garantir instalações adequadas (água limpa, sombra, espaço suficiente e alimentação correta).
    - Fiscalização: órgãos como MAPA e órgãos estaduais podem realizar inspeções.\n"""
     "Cumprir essas leis não é só obrigação legal, mas também fortalece a imagem do produtor no mercado, aumentando a confiança do consumidor.\n"
     "Quer que eu detalhe as penalidades previstas para maus-tratos ou prefere que eu explique as práticas mais recomendadas para manter a fazenda sempre dentro da lei?"
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
            return resposta
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
