from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
import fitz  # PyMuPDF
import re
from datetime import datetime

app = FastAPI()

# ---- Load and preprocess PDF ----
PDF_PATH = "Arogya Sanjeevani Policy - CIN - U10200WB1906GOI001713 1.pdf"

def load_pdf_text(pdf_path):
    text = ""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text += page.get_text()
    return text

policy_text = load_pdf_text(PDF_PATH)

# ---- Request schema ----
class QueryRequest(BaseModel):
    documents: str
    questions: list[str]

# ---- Helper: search for best matching clause ----
def find_answer_in_text(question, text):
    # Convert to lowercase for matching
    q_lower = question.lower()
    text_lower = text.lower()

    # Simple keyword search for now
    keywords = q_lower.split()
    matches = []
    for kw in keywords:
        if kw in text_lower:
            # Find all matches of keyword in text
            for match in re.finditer(kw, text_lower):
                start = max(0, match.start() - 120)
                end = min(len(text), match.end() + 120)
                matches.append(text[start:end])

    # Combine and return
    if matches:
        answer = " ... ".join(set(matches))
        return answer.strip()
    else:
        return "No relevant clause found in document."

# ---- Routes ----
@app.get("/")
async def root():
    return {"service": "LexiSearch HackRx stub", "status": "ok"}

@app.post("/hackrx/run")
async def hackrx_run(req: QueryRequest, request: Request):
    # Check auth header
    auth_header = request.headers.get("Authorization")
    if auth_header != "Bearer 4fddc1a80ba6d298647a5ff82362fac33a5920e31fa1a13650d36c693570cee7":
        raise HTTPException(status_code=401, detail="Unauthorized")

    answers = []
    for q in req.questions:
        answer = find_answer_in_text(q, policy_text)
        answers.append({
            "question": q,
            "answer": answer,
            "sources": [req.documents],
            "rationale": "Answer extracted from Arogya Sanjeevani Policy PDF using keyword search."
        })

    return {
        "answers": answers,
        "timestamp": datetime.utcnow().isoformat()
    }
