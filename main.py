import os
import uuid
import logging
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends, Request, Security
from fastapi.security import APIKeyHeader
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from database import get_db, AnalysisRequest, engine, Base
from worker import process_financial_document

# Setup Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Setup Rate Limiter
limiter = Limiter(key_func=get_remote_address)

# Create database tables if not existing
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Financial Document Analyzer")
app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)

# Setup API Key Security
api_key_header = APIKeyHeader(name="X-Api-Key", auto_error=True)
def verify_api_key(api_key: str = Security(api_key_header)):
    expected_api_key = os.environ.get("APP_API_KEY", "dev-secret-key")
    if api_key != expected_api_key:
        logger.warning("Rejected request due to invalid API Key.")
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return api_key

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Financial Document Analyzer API is running"}

@app.post("/analyze")
@limiter.limit("5/minute")
async def analyze_financial_document_endpoint(
    request: Request,
    file: UploadFile = File(...),
    query: str = Form(default="Analyze this financial document for investment insights"),
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """Analyze financial document and provide comprehensive investment recommendations asynchronously"""
    
    file_id = str(uuid.uuid4())
    file_path = f"data/financial_document_{file_id}.pdf"
    
    try:
        os.makedirs("data", exist_ok=True)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        if not query or query.strip() == "":
            query = "Analyze this financial document for investment insights"
            
        req = AnalysisRequest(
            id=file_id,
            filename=file.filename,
            query=query.strip(),
            status="pending"
        )
        db.add(req)
        db.commit()
        db.refresh(req)
        
        try:
            process_financial_document.delay(req.id, file_path, req.query)
            logger.info(f"Dispatched task {req.id} for file {file.filename}")
        except Exception as e:
            logger.error(f"Failed to dispatch to celery: {e}", exc_info=True)
            req.status = "failed"
            req.result = f"Failed to submit task to worker: {str(e)}"
            db.commit()
            raise HTTPException(status_code=503, detail="Task queue is unavailable.")
        
        return {
            "status": "success",
            "message": "Analysis started in the background",
            "task_id": req.id,
            "filename": file.filename
        }
        
    except Exception as e:
        logger.error(f"Error processing document: {e}", exc_info=True)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as cleanup_error:
                logger.warning(f"Failed to clean up file {file_path}: {cleanup_error}")
            
        raise HTTPException(status_code=500, detail="Error processing financial document")

@app.get("/status/{task_id}")
async def get_analysis_status(task_id: str, request: Request, db: Session = Depends(get_db)):
    """Retrieve the status and result of a previously submitted analysis task"""
    
    req = db.query(AnalysisRequest).filter(AnalysisRequest.id == task_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Task not found")
        
    return {
        "task_id": req.id,
        "filename": req.filename,
        "query": req.query,
        "status": req.status,
        "result": req.result,
        "created_at": req.created_at,
        "updated_at": req.updated_at
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)