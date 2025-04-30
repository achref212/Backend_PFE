from fastapi import FastAPI, Request
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import json
from datetime import datetime
import os
from dotenv import load_dotenv

from app.sql_agent.agent_runner import run_sql_agent

load_dotenv()

app = FastAPI()
LOG_PATH = "training/log_for_finetune.jsonl"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class PromptRequest(BaseModel):
    prompt: str

@app.post("/ask")
def ask(request: PromptRequest):
    prompt = request.prompt
    result = run_sql_agent(prompt)

    if isinstance(result, str):
        return {"error": result}

    log = {
        "timestamp": datetime.now().isoformat(),
        "instruction": prompt,
        "input": f"SQL : {result['sql_query']}\nRésultat brut : {result['raw_result']}",
        "output": result["summary"]
    }

    # ✅ Créer le dossier `training/` s'il n'existe pas
    os.makedirs("training", exist_ok=True)

    # ✅ Ensuite écrire le fichier log
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(log, ensure_ascii=False) + "\n")

    return result