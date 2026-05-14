import os
from dotenv import load_dotenv

from langchain_core.messages import HumanMessage, SystemMessage
from sqlalchemy import create_engine, text
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_postgres import PGVector
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from langchain_core.documents import Document

load_dotenv()

ACTIVE_PROVIDER = os.getenv("ACTIVE_PROVIDER", "openai").lower()

SYSTEM_PROMPT_TEMPLATE = """
CONTEXTO:
{contexto}

REGRAS:
- Responda somente com base no CONTEXTO.
- Se a informação não estiver explicitamente no CONTEXTO, responda:
  "Não tenho informações necessárias para responder sua pergunta."
- Nunca invente ou use conhecimento externo.
- Nunca produza opiniões ou interpretações além do que está escrito.

EXEMPLOS DE PERGUNTAS FORA DO CONTEXTO:
Pergunta: "Qual é a capital da França?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Quantos clientes temos em 2024?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Você acha isso bom ou ruim?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."
"""

_prompt = PromptTemplate(
    input_variables=["contexto", "history", "question"],
    template=SYSTEM_PROMPT_TEMPLATE,
)

_embeddings = None
_llm = None


def search_documents(query: str) -> str:
    """Search the internal document store and return relevant passages for the given query."""
    store = PGVector(
        embeddings=_embeddings, # type: ignore
        collection_name=os.getenv("PG_VECTOR_COLLECTION_NAME"), # type: ignore
        connection=os.getenv("DATABASE_URL"),
        use_jsonb=True,
    )
    results = store.similarity_search_with_score(query, k=10)
    return "\n\n".join(doc.page_content for doc, _score in results)


def build_db_context_summary(llm) -> str:
    """Fetch all documents from the DB and summarize them via Map-Reduce."""
    engine = create_engine(os.getenv("DATABASE_URL")) # type: ignore
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT e.document
            FROM langchain_pg_embedding e
            JOIN langchain_pg_collection c ON e.collection_id = c.uuid
            WHERE c.name = :name
            ORDER BY e.id
        """), {"name": os.getenv("PG_VECTOR_COLLECTION_NAME")}).fetchall()

    if not rows:
        return ""

    docs = [Document(page_content=row[0]) for row in rows]

    map_prompt = PromptTemplate.from_template(
        "Escreva um resumo conciso do seguinte trecho:\n{contexto}"
    )
    map_chain = map_prompt | llm | StrOutputParser()

    reduce_prompt = PromptTemplate.from_template(
        "Combine os seguintes resumos em um único resumo conciso:\n{contexto}"
    )
    reduce_chain = reduce_prompt | llm | StrOutputParser()

    prepare_map_inputs = RunnableLambda(lambda d: [{"contexto": doc.page_content} for doc in d])
    prepare_reduce_input = RunnableLambda(lambda summaries: {"contexto": "\n".join(summaries)})

    pipeline = prepare_map_inputs | map_chain.map() | prepare_reduce_input | reduce_chain

    return pipeline.invoke(docs)


def init_agent_from_config() -> str:
    """Inicializa os modelos baseados no provedor definido no .env"""
    global _llm, _embeddings
    
    # Validação simples no banco apenas para garantir que existem dados lá (ignora dimensões)
    engine = create_engine(os.getenv("DATABASE_URL"))
    with engine.connect() as conn:
        row = conn.execute(text("""
            SELECT 1
            FROM langchain_pg_embedding e
            JOIN langchain_pg_collection c ON e.collection_id = c.uuid
            WHERE c.name = :name
            LIMIT 1
        """), {"name": os.getenv("PG_VECTOR_COLLECTION_NAME")}).fetchone()

    if row is None:
        raise RuntimeError("Nenhum embedding encontrado no banco. Execute o script de ingestão primeiro.")

    # Verificação do modelo ativo
    if ACTIVE_PROVIDER == "openai":
        _embeddings = OpenAIEmbeddings(model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"))
        _llm = ChatOpenAI(model=os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini"))
        return "OpenAI ativado"
        
    elif ACTIVE_PROVIDER in ["google", "gemini"]:
        _embeddings = GoogleGenerativeAIEmbeddings(model=os.getenv("GOOGLE_EMBEDDING_MODEL", "models/text-embedding-004"))
        _llm = ChatGoogleGenerativeAI(model=os.getenv("GOOGLE_CHAT_MODEL", "gemini-1.5-flash"))
        return "Google Gemini ativado"
        
    else:
        raise ValueError(f"Provedor desconhecido: '{ACTIVE_PROVIDER}'. Configure ACTIVE_PROVIDER como 'openai' ou 'google' no seu .env.")


_session_store: dict[str, InMemoryChatMessageHistory] = {}


def _get_session_history(session_id: str) -> InMemoryChatMessageHistory:
    if session_id not in _session_store:
        _session_store[session_id] = InMemoryChatMessageHistory()
    return _session_store[session_id]


def search_prompt(question: str, session_id: str = "default") -> str:
    # 1. Recupera o histórico da sessão
    history = _get_session_history(session_id)

    # 2. Busca os documentos no banco para formar o contexto
    contexto = search_documents(question)

    # 3. Formata a mensagem de Sistema (Regras + Contexto)
    system_text = SYSTEM_PROMPT_TEMPLATE.format(contexto=contexto)

    # 4. Monta o Array Estruturado de Mensagens
    messages = [SystemMessage(content=system_text)]

    # Adiciona as mensagens antigas da conversa
    messages.extend(history.messages) # type: ignore
    
    # Adiciona a pergunta atual do usuário
    messages.append(HumanMessage(content=question)) # type: ignore

    # 5. Invoca o LLM passando a lista de mensagens
    raw = _llm.invoke(messages).content # type: ignore

    if isinstance(raw, list):
        answer = next((b["text"] for b in raw if isinstance(b, dict) and b.get("type") == "text"), str(raw))
    else:
        answer = raw

    # 6. Salva a nova interação no histórico
    history.add_user_message(question)
    history.add_ai_message(answer)

    return answer
