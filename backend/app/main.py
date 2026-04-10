from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from supabase import create_client
import anthropic

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


@app.get("/test/anthropic")
async def test_anthropic():
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=50,
        messages=[{"role": "user", "content": "Say 'connection successful' and nothing else."}]
    )
    return {"status": "connected", "response": message.content[0].text}