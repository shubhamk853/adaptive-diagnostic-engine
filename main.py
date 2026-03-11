from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uuid

app = FastAPI(title="Adaptive Diagnostic Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Fake database (no MongoDB needed)
questions = [
    {"id": "q1", "prompt": "3x+5=20, x=?", "options": ["3", "4", "5", "7"], "correct": "5", "difficulty": 0.4, "topic": "Algebra"},
    {"id": "q2", "prompt": "'aberrant' means?", "options": ["normal", "deviant", "pleasant", "ancient"], "correct": "deviant", "difficulty": 0.5, "topic": "Vocabulary"}
]
sessions = {}

class Question(BaseModel):
    id: str
    prompt: str
    options: List[str]
    difficulty: float
    topic: str

class StartResponse(BaseModel):
    session_id: str
    question: Question

class AnswerRequest(BaseModel):
    session_id: str
    question_id: str
    chosen_option: str

class AnswerResponse(BaseModel):
    correct: bool
    ability_estimate: float
    next_question: Optional[Question] = None
    is_finished: bool

@app.get("/")
def root():
    return {"message": "✅ Adaptive Engine Running Perfectly!"}

@app.post("/start-session", response_model=StartResponse)
def start_session(user_id: str = "demo"):
    session_id = str(uuid.uuid4())
    question = questions[0]
    sessions[session_id] = {
        "ability": 0.5,
        "questions_asked": 0,
        "max_questions": 3,
        "current_question": "q1"
    }
    return StartResponse(session_id=session_id, question=Question(**question))

@app.post("/submit-answer", response_model=AnswerResponse)
def submit_answer(request: AnswerRequest):
    if request.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[request.session_id]
    question = next(q for q in questions if q["id"] == request.question_id)
    
    correct = request.chosen_option == question["correct"]
    # Simple adaptive logic
    if correct:
        session["ability"] = min(1.0, session["ability"] + 0.1)
    else:
        session["ability"] = max(0.0, session["ability"] - 0.1)
    
    session["questions_asked"] += 1
    is_finished = session["questions_asked"] >= session["max_questions"]
    
    next_question = None
    if not is_finished:
        next_idx = 1 if session["current_question"] == "q1" else 0
        next_q_data = questions[next_idx]
        session["current_question"] = next_q_data["id"]
        next_question = Question(**next_q_data)
    
    return AnswerResponse(
        correct=correct,
        ability_estimate=session["ability"],
        next_question=next_question,
        is_finished=is_finished
    )

@app.get("/study-plan/{session_id}")
def get_study_plan(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    ability = sessions[session_id]["ability"]
    steps = [
        "Practice 10 medium difficulty questions daily",
        "Focus on weak topics identified in this test", 
        "Take 2 full-length timed mock tests"
    ]
    
    return {
        "ability_estimate": ability,
        "study_plan": steps
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
