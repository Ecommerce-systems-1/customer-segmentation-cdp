from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import pathlib
from app.database import get_db
from app.routers import customers
from app.routers.customers import refresh_segments

app = FastAPI(title="Customer Segmentation CDP")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(customers.router)

get_db()
refresh_segments()  # segment on import; tests use TestClient without lifespan


@app.get("/health")
def health():
    db = get_db()
    total = db.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    segmented = db.execute("SELECT COUNT(*) FROM customers WHERE segment IS NOT NULL").fetchone()[0]
    return {"status": "ok", "customers": total, "segmented": segmented}


static_dir = pathlib.Path("/app/frontend/out")
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
