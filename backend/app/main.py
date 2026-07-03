from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import pathlib
from app.database import get_db
from app.routers import accounts
from app.routers.accounts import refresh_scores

app = FastAPI(title="B2B Customer Segmentation & Churn Predictor")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(accounts.router)

get_db()
refresh_scores()  # segment + score on import; tests use TestClient without lifespan


@app.get("/health")
def health():
    db = get_db()
    total = db.execute("SELECT COUNT(*) FROM accounts").fetchone()[0]
    segmented = db.execute("SELECT COUNT(*) FROM accounts WHERE segment IS NOT NULL").fetchone()[0]
    scored = db.execute("SELECT COUNT(*) FROM accounts WHERE churn_probability IS NOT NULL").fetchone()[0]
    return {"status": "ok", "accounts": total, "segmented": segmented, "churn_scored": scored}


static_dir = pathlib.Path("/app/frontend/out")
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
