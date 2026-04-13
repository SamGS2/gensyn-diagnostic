from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from supabase import create_client


load_dotenv()

app = FastAPI(
    title="Gensyn Diagnostic Tool",
    description="Framework-based diagnostic for identifying organizational stuck points",
    version="0.1.0",
)

# Allow frontend to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "https://diagnostic.gensyn.co",  # Production subdomain (update when known)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"status": "ok", "service": "Gensyn Diagnostic Tool"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
    from supabase import create_client
import anthropic

@app.get("/test/supabase")
async def test_supabase():
    supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
    result = supabase.table("sessions").select("id").limit(1).execute()
    return {"status": "connected", "data": result.data}


