import hashlib
import os

from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from langchain_text_splitters import RecursiveCharacterTextSplitter


load_dotenv()

PDF_PATH = os.getenv("PDF_PATH")
GOOGLE_EMBEDDING_MODEL = os.getenv("GOOGLE_EMBEDDING_MODEL", "models/embedding-001")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
DATABASE_URL = os.getenv("DATABASE_URL", "rag")
COLLECTION_NAME = os.getenv("PG_VECTOR_COLLECTION_NAME", "rag")

def choose_embeddings_model():
    """
    Função que permite escolher o modelo de embeddings dinamicamente
    """
    print("\nEscolha um modelo dentre os modelos de embeddings disponíveis:")
    print(f"1 - Gemini ({GOOGLE_EMBEDDING_MODEL})")
    print(f"2 - OpenAI ({OPENAI_EMBEDDING_MODEL})")

    while True:

        choice = input("\nOpção (1 ou 2): ").strip()

        if choice == "1":
            return GoogleGenerativeAIEmbeddings(model=GOOGLE_EMBEDDING_MODEL)
        elif choice == "2":
            return OpenAIEmbeddings(model=OPENAI_EMBEDDING_MODEL)

        print("❌Opção inválida. Digite 1 ou 2.")

def generate_deterministic_id(content, file_path):
    """
    Gera ID único baseado no conteúdo para evitar duplicatas no banco. Evitará indexações duplicadas.
    """
    hash_obj = hashlib.md5(f"{file_path}-{content}".encode())
    return f"doc-{hash_obj.hexdigest()}"


def ingest_pdf():
    """
    Função para ingestão do PDF
    """
    # Validação de arquivo
    if not PDF_PATH or not os.path.exists(PDF_PATH):
        print(f"❌ Erro: Arquivo PDF não encontrado no caminho: {PDF_PATH}")
        return

    print(f"📄 Carregando PDF: {PDF_PATH}...")
    loader = PyPDFLoader(str(PDF_PATH))
    docs = loader.load()

    # Divisão do texto em blocos (Chunks)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        add_start_index=True,
    )
    splits = text_splitter.split_documents(docs)

    if not splits:
        print("⚠️ Nenhum conteúdo extraído do PDF.")
        return

    print(f"✂️ Documento dividido em {len(splits)} blocos.")

    # Preparação dos documentos e IDs únicos
    enriched_docs = []
    doc_ids = []

    for split in splits:
        # Limpeza de metadados
        clean_metadata = {k: v for k, v in split.metadata.items() if v not in ("", None)}

        doc = Document(
            page_content=split.page_content,
            metadata=clean_metadata
        )

        # Gerar ID baseado no conteúdo para evitar duplicidade se rodar o script de novo
        unique_id = generate_deterministic_id(split.page_content, PDF_PATH)

        enriched_docs.append(doc)
        doc_ids.append(unique_id)

    # Seleção do modelo de IA
    embeddings = choose_embeddings_model()

    # Conexão com o Vector Store (PostgreSQL + PGVector)
    try:
        print("🗄️ Conectando ao banco de dados e enviando vetores...")
        store = PGVector(
            embeddings=embeddings,
            collection_name=COLLECTION_NAME,
            connection=DATABASE_URL,
            use_jsonb=True,
        )

        store.add_documents(documents=enriched_docs, ids=doc_ids)
        print("✅ Ingestão concluída com sucesso!")

    except Exception as e:
        print(f"❌ Erro ao conectar ou salvar no banco de dados: {e}")

if __name__ == "__main__":
    ingest_pdf()
