import os
import fitz  # PyMuPDF
from google import genai
from core.db import get_connection
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs_raw")

def extract_text_from_pdf(pdf_path):
    """Extrae texto preservando estructura usando PyMuPDF (Seguridad Nivel 1%)."""
    text_chunks = []
    try:
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text("text")
            if text.strip():
                # Enfoque simple: 1 chunk por página (o podría dividirse recursivamente si es muy largo)
                text_chunks.append(f"--- Página {page_num + 1} ---\n{text.strip()}")
        doc.close()
    except Exception as e:
        print(f"Error parseando {pdf_path}: {e}")
    return text_chunks

async def process_and_seed():
    print("🌱 Iniciando siembra de conocimiento PGVector...")
    if not os.path.exists(DOCS_DIR):
        print(f"La carpeta {DOCS_DIR} no existe. Créala y coloca los PDFs.")
        return

    conn = get_connection()
    cur = conn.cursor()

    # Asegurar extensión pgvector iterativa
    # (Asumiendo que memoria_vectorial ya fue creada en schema.sql, o creándola on the fly)
    try:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS memoria_vectorial (
                id SERIAL PRIMARY KEY,
                titulo_doc VARCHAR(255),
                contenido TEXT,
                embedding vector(768)
            );
        """)
        conn.commit()
    except Exception as dbe:
        print(f"Aviso de Base de Datos: {dbe}")
        conn.rollback()

    for filename in os.listdir(DOCS_DIR):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(DOCS_DIR, filename)
            print(f"📄 Procesando: {filename}")
            
            chunks = extract_text_from_pdf(pdf_path)
            for i, chunk in enumerate(chunks):
                if len(chunk) < 50: continue # Skip empty/meaningless
                
                print(f"  🧠 Generando embedding para chunk {i+1}/{len(chunks)}...")
                try:
                    # Usamos el modelo de embeddings de Gemini
                    response = client.models.embed_content(
                        model="text-embedding-004",
                        contents=chunk
                    )
                    
                    # Gemini Text Embedding return list of floats
                    embedding = response.embeddings[0].values
                    
                    cur.execute("""
                        INSERT INTO memoria_vectorial (titulo_doc, contenido, embedding)
                        VALUES (%s, %s, %s::vector)
                    """, (filename, chunk, embedding))
                    conn.commit()
                except Exception as e:
                    print(f"Error generando/insertando embedding: {e}")
                    conn.rollback()
                    
    cur.close()
    conn.close()
    print("✅ Siembra de conocimiento completada.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(process_and_seed())
