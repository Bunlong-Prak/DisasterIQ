from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
from data_ingestion import ingest_gdacs, ingest_fema
from chat import router as chat_router
from alerts import router as alerts_router

app = FastAPI(title="DisasterIQ API")

app.include_router(chat_router, prefix="/chat")
app.include_router(alerts_router, prefix="/alerts")

scheduler = BackgroundScheduler()

@app.on_event("startup")
def startup():
    # Poll GDACS every 6 minutes (matches their update frequency)
    scheduler.add_job(ingest_gdacs, "interval", minutes=6)
    # Poll FEMA every hour
    scheduler.add_job(ingest_fema, "interval", hours=1)
    scheduler.start()
    # Run once on startup
    ingest_gdacs()
    ingest_fema()

@app.on_event("shutdown")
def shutdown():
    scheduler.shutdown()

@app.get("/health")
def health():
    return {"status": "ok"}
