import os
import time
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from tqdm.auto import tqdm
from pinecone import Pinecone, ServerlessSpec
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from ..config.db import reports_collection
from typing import List
from fastapi import UploadFile, HTTPException

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENV", "us-east-1")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploaded_reports")

os.makedirs(UPLOAD_DIR, exist_ok=True)


async def load_vectorstore(uploaded_files:List[UploadFile],uploaded:str,doc_id:str):
    """
    Save files, chunk texts, embed texts, upsert in Pinecone and write metadata to Mongo
    """
    # Validate required configuration
    missing_vars = [name for name, val in (
        ("PINECONE_API_KEY", PINECONE_API_KEY),
        ("PINECONE_INDEX_NAME", PINECONE_INDEX_NAME),
    ) if not val]
    if missing_vars:
        raise HTTPException(status_code=500, detail=f"Missing environment variables: {', '.join(missing_vars)}")
    # Help static type-checkers: ensure non-None string is used for index name
    index_name: str = str(PINECONE_INDEX_NAME)

    try:
        # Lazy initialize Pinecone per request to avoid startup failures
        pc = Pinecone(api_key=PINECONE_API_KEY)
        spec = ServerlessSpec(cloud="aws", region=PINECONE_ENV)
        # Initialize embedding model (Hugging Face SentenceTransformer)
        embed_model = SentenceTransformer("sentence-transformers/embeddinggemma-300m-medical")
        embedding_dim = embed_model.get_sentence_embedding_dimension()

        existing_indexes = [i["name"] for i in pc.list_indexes()]
        if index_name not in existing_indexes:
            pc.create_index(name=index_name, dimension=embedding_dim, metric="dotproduct", spec=spec)
            while not pc.describe_index(index_name).status["ready"]:
                time.sleep(1)
        index = pc.Index(index_name)

        # embed_model already initialized above

        total_chunks = 0
        processed_files = []

        for file in uploaded_files:
            # UploadFile.filename can be None; coerce to a safe default
            safe_filename = (file.filename or "upload.bin")
            filename = Path(safe_filename).name
            save_path = Path(UPLOAD_DIR) / f"{doc_id}_{filename}"
            content = await file.read()
            with open(save_path, "wb") as f:
                f.write(content)

            # load pdf pages for the current file
            loader = PyPDFLoader(str(save_path))
            documents = loader.load()
            splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
            chunks = splitter.split_documents(documents)

            if not chunks:
                continue

            texts = [chunk.page_content for chunk in chunks]
            ids = [f"{doc_id}-{len(processed_files)}-{i}" for i in range(len(chunks))]
            metadatas = [
                {
                    "source": filename,
                    "doc_id": doc_id,
                    "uploader": uploaded,
                    "page": chunk.metadata.get("page", None),
                    "text": chunk.page_content[:2000]
                }
                for chunk in chunks
            ]

            # get embeddings and upsert
            embeddings = await asyncio.to_thread(embed_model.encode, texts, convert_to_numpy=True, normalize_embeddings=False)
            def upsert():
                index.upsert(vectors=list(zip(ids, embeddings, metadatas)))
            await asyncio.to_thread(upsert)

            total_chunks += len(chunks)
            processed_files.append(filename)

        if not processed_files:
            raise HTTPException(status_code=400, detail="No valid files were processed. Ensure PDFs are uploaded.")

        # save report metadata in mongo per request
        reports_collection.insert_one({
            "doc_id": doc_id,
            "filenames": processed_files,
            "uploader": uploaded,
            "num_chunks": total_chunks,
            "uploaded_at": time.time()
        })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload processing failed: {e}")