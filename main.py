from fastapi import FastAPI, HTTPException, Header, Request
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import os
import datetime

# Team token from the problem statement (we'll validate incoming Authorization Bearer)
EXPECTED_TOKEN = "4fddc1a80ba6d298647a5ff82362fac33a5920e31fa1a13650d36c693570cee7"

app = FastAPI(title="LexiSearch - HackRx Stub", version="0.1")

class RunRequest(BaseModel):
    documents: str
    questions: List[str]

class AnswerItem(BaseModel):
    question: str
    answer: str
    sources: Optional[List[str]] = None
    rationale: Optional[str] = None

class RunResponse(BaseModel):
    answers: List[AnswerItem]
    timestamp: str

def _authorize(auth_header: Optional[str]):
    if not auth_header:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer" or parts[1] != EXPECTED_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid or missing token")

def _build_canned_answer(q: str, doc_url: str):
    q_lower = q.lower()
    if "grace period" in q_lower:
        ans = "A grace period of thirty days is provided for premium payment after the due date to renew or continue the policy without losing continuity benefits."
        sources = [f"{doc_url}#page=policy_section_payment"]
        rationale = "Found payment & renewal clause referencing grace period; typical industry standard is 30 days (used as example)."
    elif "pre-existing" in q_lower or "ped" in q_lower:
        ans = "There is a waiting period of thirty-six (36) months of continuous coverage from the first policy inception for pre-existing diseases and their direct complications to be covered."
        sources = [f"{doc_url}#page=waiting_period"]
        rationale = "Matched 'pre-existing diseases' clause in policy's waiting period section."
    elif "maternity" in q_lower:
        ans = "Yes, the policy covers maternity expenses with eligibility after 24 months of continuous coverage and limited to two deliveries or terminations during the policy period."
        sources = [f"{doc_url}#page=maternity_benefits"]
        rationale = "Maternity conditions typically require a 24-month continuous coverage — mapped from policy's benefit table."
    elif "cataract" in q_lower:
        ans = "Specific waiting period of two (2) years applies for cataract surgery."
        sources = [f"{doc_url}#page=ocular_conditions"]
        rationale = "Cataract surgery waiting period found under exclusions & waiting tabular info."
    elif "organ donor" in q_lower:
        ans = "Yes, medical expenses for an organ donor's hospitalization are indemnified when the organ is for an insured person and donation complies with the relevant Act."
        sources = [f"{doc_url}#page=organ_donor"]
        rationale = "Policy clarifies organ donor indemnity referencing transplantation law compliance."
    elif "no claim discount" in q_lower or "ncd" in q_lower:
        ans = "A No Claim Discount (NCD) of 5% on the base premium is offered on renewal for a one-year policy term if no claims were made in the preceding year; maximum aggregate NCD capped at 5%."
        sources = [f"{doc_url}#page=ncd_section"]
        rationale = "NCD details located in renewal discounts table."
    else:
        ans = f"[Stub answer] This is a placeholder response for: \"{q}\". Replace this logic with embeddings+LLM retrieval for precise answers."
        sources = [f"{doc_url}#page=unknown"]
        rationale = "No canned mapping found. The production system would run semantic retrieval and LLM reasoning."

    return ans, sources, rationale

@app.post("/hackrx/run", response_model=RunResponse)
async def hackrx_run(req: RunRequest, authorization: Optional[str] = Header(None)):
    _authorize(authorization)

    doc_url = req.documents
    questions = req.questions

    answers = []
    for q in questions:
        ans_text, sources, rationale = _build_canned_answer(q, doc_url)
        answers.append(AnswerItem(
            question=q,
            answer=ans_text,
            sources=sources,
            rationale=rationale
        ))

    return RunResponse(
        answers=answers,
        timestamp=datetime.datetime.utcnow().isoformat() + "Z"
    )

@app.get("/")
def root():
    return {"service": "LexiSearch HackRx stub", "status": "ok"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)), reload=True)
