import hashlib
import os

from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy import create_engine, text


load_dotenv()

PDF_PATH = os.getenv("PDF_PATH")
GOOGLE_EMBEDDING_MODEL = os.getenv("GOOGLE_EMBEDDING_MODEL", "models/text-embedding-004")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
DATABASE_URL = os.getenv("DATABASE_URL")
COLLECTION_NAME = os.getenv("PG_VECTOR_COLLECTION_NAME", "rag")


def choose_embeddings_model():
    """Permite escolher o modelo de embeddings dinamicamente."""
    print("\nEscolha um modelo dentre os modelos de embeddings disponíveis:")
    print(f"1 - Gemini ({GOOGLE_EMBEDDING_MODEL})")
    print(f"2 - OpenAI ({OPENAI_EMBEDDING_MODEL})")

    while True:
        choice = input("\nOpção (1 ou 2): ").strip()
        if choice == "1":
            return GoogleGenerativeAIEmbeddings(model=GOOGLE_EMBEDDING_MODEL)
        elif choice == "2":
            return OpenAIEmbeddings(model=OPENAI_EMBEDDING_MODEL)
        print("❌ Opção inválida. Digite 1 ou 2.")


def generate_deterministic_id(content, file_path):
    """Gera ID único baseado no conteúdo para evitar duplicatas."""
    hash_obj = hashlib.md5(f"{file_path}-{content}".encode())
    return f"doc-{hash_obj.hexdigest()}"


def get_existing_ids(db_url, collection_name, doc_ids):
    """
    Conecta ao banco e verifica quais dos IDs fornecidos já existem na coleção.
    Retorna um 'set' (conjunto) com os IDs que já estão no banco.
    """
    engine = create_engine(db_url)
    try:
        with engine.connect() as conn:
            # 1. Busca o UUID da coleção atual
            query_col = text("SELECT uuid FROM langchain_pg_collection WHERE name = :name")
            col_id = conn.execute(query_col, {"name": collection_name}).scalar()

            if not col_id:
                # Se a coleção não existe, nenhum ID existe ainda
                return set()

            # 2. Busca quais dos nossos IDs já estão na tabela de embeddings
            query_ids = text("""
                SELECT id FROM langchain_pg_embedding
                WHERE collection_id = :col_id AND id = ANY(:ids)
            """)
            result = conn.execute(query_ids, {"col_id": col_id, "ids": doc_ids}).fetchall()

            # Retorna um conjunto apenas com os IDs encontrados
            return {row[0] for row in result}

    except Exception as e:
        print(
            f"⚠️ Aviso: Não foi possível checar o banco (pode estar vazio ou não inicializado). Assumindo que não há duplicatas. Detalhe: {e}"
        )
        return set()


def ingest_pdf():
    # Validação de arquivo
    if not PDF_PATH or not os.path.exists(PDF_PATH):
        print(f"❌ Erro: Arquivo PDF não encontrado no caminho: {PDF_PATH}")
        return

    print(f"📄 Carregando PDF: {PDF_PATH}...")
    loader = PyPDFLoader(str(PDF_PATH))
    docs = loader.load()

    # Divisão do texto em blocos
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        add_start_index=True,
    )
    splits = text_splitter.split_documents(docs)

    if not splits:
        print("⚠️ Nenhum conteúdo extraído do PDF.")
        return

    print(f"✂️ Documento dividido em {len(splits)} blocos. Preparando IDs...")

    # Prepara todos os documentos e IDs
    all_docs = []
    all_ids = []

    for split in splits:
        clean_metadata = {k: v for k, v in split.metadata.items() if v not in ("", None)}
        doc = Document(page_content=split.page_content, metadata=clean_metadata)
        unique_id = generate_deterministic_id(split.page_content, PDF_PATH)

        all_docs.append(doc)
        all_ids.append(unique_id)

    print("🔍 Verificando no banco de dados quais blocos já foram indexados...")
    existing_ids = get_existing_ids(DATABASE_URL, COLLECTION_NAME, all_ids)

    docs_to_insert = []
    ids_to_insert = []

    # Filtra apenas os documentos que NÃO estão no banco
    for doc, doc_id in zip(all_docs, all_ids, strict=True):
        if doc_id not in existing_ids:
            docs_to_insert.append(doc)
            ids_to_insert.append(doc_id)

    if not docs_to_insert:
        print("✅ Todos os blocos deste PDF já estão indexados no banco. Nenhuma ação necessária!")
        return

    print(f"🚀 Encontrados {len(docs_to_insert)} blocos novos. Iniciando geração de embeddings...")

    # Só pedimos para o usuário escolher o modelo se realmente houver algo novo para indexar
    embeddings = choose_embeddings_model()

    try:
        store = PGVector(
            embeddings=embeddings,
            collection_name=COLLECTION_NAME,
            connection=DATABASE_URL,
            use_jsonb=True,
        )

        store.add_documents(documents=docs_to_insert, ids=ids_to_insert)
        print(f"✨ Sucesso! {len(docs_to_insert)} novos blocos foram indexados.")

    except Exception as e:
        print(f"❌ Erro ao conectar ou salvar no banco de dados: {e}")


if __name__ == "__main__":
    ingest_pdf()
