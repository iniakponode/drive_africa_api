"""
Background tasks for analytics pre-computation.
"""
from safedrive.celery_app import celery_app
from safedrive.database.session import SessionLocal
from safedrive.api.v1.endpoints.analytics import bad_days
from safedrive.core.cache import cache_set, CACHE_TTL_LONG
import logging

logger = logging.getLogger(__name__)


@celery_app.task(name="precompute_bad_days")
def precompute_bad_days_task():
    """
    Pre-compute bad days for all cohorts and cache results.
    Runs every 15 minutes via Celery Beat.
    """
    db = SessionLocal()
    
    try:
        # Common cohorts to pre-compute (add your fleet IDs)
        cohorts_to_precompute = [
            None,  # All drivers
            # Add specific fleet IDs if needed
        ]
        
        for cohort in cohorts_to_precompute:
            for page in range(1, 6):  # Pre-compute first 5 pages
                logger.info(f"Pre-computing bad_days: cohort={cohort}, page={page}")
                
                # This will compute and cache
                # Note: You'll need to refactor bad_days to accept db session
                result = bad_days(
                    fleet_id=cohort,
                    insurance_partner_id=None,
                    page=page,
                    page_size=25,
                    db=db,
                    current_client=None  # Admin context
                )
                
                logger.info(f"Pre-computed {len(result.drivers)} drivers")
        
        logger.info("Bad days pre-computation complete")
        return {"status": "success", "cohorts_processed": len(cohorts_to_precompute)}
        
    except Exception as e:
        logger.error(f"Bad days pre-computation failed: {e}")
        raise
    finally:
        db.close()


# Celery Beat schedule (cron-like)
celery_app.conf.beat_schedule = {
    'precompute-bad-days-every-15-min': {
        'task': 'precompute_bad_days',
        'schedule': 900.0,  # 15 minutes
    },
}
