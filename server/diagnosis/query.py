import os
import asyncio
from dotenv import load_dotenv
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.language_models.chat_models import BaseChatModel

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "rbac-diagnosis-index")
EMBED_MODEL_NAME = os.getenv("EMBED_MODEL_NAME", "sentence-transformers/embeddinggemma-300m-medical")
pc=Pinecone(api_key=PINECONE_API_KEY)
index=pc.Index(PINECONE_INDEX_NAME)

embed_model = SentenceTransformer(EMBED_MODEL_NAME)
llm: BaseChatModel = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

prompt=PromptTemplate.from_template(
    """
You are a medical assistant. Using only the provided context (portions of the user's report), produce:
1) A concise probable diagnosis (4 - 5 lines)
2) Key major findings from the report (bullet points)
3) Recommended next steps (tests/treatments) — label clearly as suggestions, not medical advice.

Context:
{context_text}

User question:
{question}
""")

rag_chain=prompt | llm

async def diagnosis_report(user:str,doc_id:str,question:str):
    # embed question
    embedding=await asyncio.to_thread(embed_model.encode, question, convert_to_numpy=True, normalize_embeddings=False)
    # query pinecone
    results=await asyncio.to_thread(index.query,vector=embedding.tolist(),top_k=5,include_metadata=True)

    # filter for doc_id matches
    contexts=[]
    sources_set=set()
    for match in results.get("matches",[]):
        md=match.get("metadata",{})
        if md.get("doc_id") == doc_id:
            # take text snippet 
            text_snippet=md.get("text") or ""
            contexts.append(text_snippet)
            sources_set.add(md.get("source"))

    if not contexts:
        return {"diagnosis":None,"explanation":"No report contentindexed for this doc_id"}
    
    # limit context length
    context_text="\n\n".join(contexts[:5])

    # final call the rag chain
    final=await asyncio.to_thread(rag_chain.invoke,{"context_text":context_text,"question":question})

    return {"diagnosis":final.content,"sources":list(sources_set)}