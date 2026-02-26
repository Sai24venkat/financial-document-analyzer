import os
import logging
from celery import Celery
from crewai import Crew, Process
from database import SessionLocal, AnalysisRequest

# Import agents and tasks
from agents import financial_analyst, verifier, investment_advisor, risk_assessor
from task import verification, analyze_financial_document, investment_analysis, risk_assessment

# Setup Logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Initialize Celery app
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
celery_app = Celery("financial_worker", broker=REDIS_URL, backend=REDIS_URL)

@celery_app.task(
    name="process_financial_document",
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3},
    retry_backoff=True,
    retry_jitter=True
)
def process_financial_document(self, request_id: str, file_path: str, query: str):
    db = SessionLocal()
    req = db.query(AnalysisRequest).filter(AnalysisRequest.id == request_id).first()
    
    # Idempotency Check
    if not req or req.status in ["completed", "failed"]:
        db.close()
        logger.info(f"Task {request_id} already processed or invalid.")
        return "Task already processed or invalid"

    req.status = "processing"
    db.commit()

    try:
        logger.info(f"Starting analysis for task {request_id}")
        financial_crew = Crew(
            agents=[verifier, financial_analyst, investment_advisor, risk_assessor],
            tasks=[verification, analyze_financial_document, investment_analysis, risk_assessment],
            process=Process.sequential,
        )
        
        enhanced_query = f"Task Query: {query} | Document Path: {file_path}"
        
        result = financial_crew.kickoff({'query': enhanced_query})
        
        req.status = "completed"
        req.result = str(result)
        db.commit()
        logger.info(f"Task {request_id} completed successfully.")
    except Exception as e:
        logger.error(f"[Task {request_id}] Error processing document: {str(e)}", exc_info=True)
        req.status = "failed"
        req.result = f"Error processing document: {str(e)}"
        db.commit()
        # Reraise so celery knows it failed and will retry
        raise e
    finally:
        # Clean up the file after processing
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as cleanup_error:
                logger.warning(f"Failed to clean up file {file_path}: {cleanup_error}")
        db.close()

    return "Done"
