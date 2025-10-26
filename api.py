from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from models import SessionLocal, Resume, Employer, init_db
from config import ADMIN_API_KEY
from typing import List, Optional
import os

init_db()
app = FastAPI(title="ResumeBot API")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def check_admin(key: str):
    if key != ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")

@app.get("/search")
def search_resumes(q: Optional[str] = Query(None), lang: Optional[str] = None, consent_only: bool = True, api_key: str = ""):
    check_admin(api_key)
    db = SessionLocal()
    query = db.query(Resume)
    if consent_only:
        query = query.filter(Resume.consent_for_employers == True)
    if lang:
        # join user table to filter by user.lang if needed
        query = query.join(Resume.user).filter_by(lang=lang)
    if q:
        likeq = f"%{q.lower()}%"
        query = query.filter(
            (Resume.name.ilike(likeq)) |
            (Resume.position.ilike(likeq)) |
            (Resume.skills.ilike(likeq)) |
            (Resume.city.ilike(likeq))
        )
    results = query.order_by(Resume.created_at.desc()).limit(200).all()
    out = []
    for r in results:
        out.append({
            "id": r.id,
            "name": r.name,
            "position": r.position,
            "city": r.city,
            "experience": r.experience,
            "skills": r.skills,
            "pdf": f"/download/{r.id}"
        })
    db.close()
    return {"results": out}

@app.get("/download/{resume_id}")
def download_resume(resume_id: int, api_key: str = ""):
    check_admin(api_key)
    db = SessionLocal()
    r = db.query(Resume).get(resume_id)
    db.close()
    if not r or not r.pdf_path or not os.path.exists(r.pdf_path):
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(r.pdf_path, media_type="application/pdf", filename=os.path.basename(r.pdf_path))
