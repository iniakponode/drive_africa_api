# safedrive/api/v1/api_router.py
import logging
from fastapi import APIRouter, Depends

from safedrive.api.v1.endpoints.trip import router as trips_router
from safedrive.api.v1.endpoints.index import router as index_router
from safedrive.api.v1.endpoints.unsafe_behaviour import router as unsafe_behaviour_router
from safedrive.api.v1.endpoints.raw_sensor_data import router as raw_sensor_data_router
from safedrive.api.v1.endpoints.driver_profile import router as driver_profile_router
from safedrive.api.v1.endpoints.driving_tips import router as driving_tips_router
from safedrive.api.v1.endpoints.cause import router as cause_router
from safedrive.api.v1.endpoints.embedding import router as embedding_router
from safedrive.api.v1.endpoints.nlg_report import router as nlg_report_router
from safedrive.api.v1.endpoints.ai_model_inputs_router import router as ai_model_inputs_router
from safedrive.api.v1.endpoints.location import router as location_router
from safedrive.api.v1.endpoints.alcohol_questionnaire import (
    router as alcohol_questionnaire_router,
    mobile_router as alcohol_questionnaire_mobile_router,
)
from safedrive.api.v1.endpoints.behaviour_metrics import router as behaviour_metrics_router
from safedrive.api.v1.endpoints.fleet_monitoring import router as fleet_monitoring_router
from safedrive.api.v1.endpoints.fleet_management import router as fleet_management_router
from safedrive.api.v1.endpoints.researcher import router as researcher_router
from safedrive.api.v1.endpoints.road import router as road_router
from safedrive.api.v1.endpoints.insurance_partner import router as insurance_partner_router
from safedrive.api.v1.endpoints.admin import router as admin_router
from safedrive.core.security import Role, get_current_client, require_roles

safe_drive_africa_api_router = APIRouter()
logger = logging.getLogger(__name__)

safe_drive_africa_api_router.include_router(
    index_router,
    prefix="/api",
    tags=["Index"],
    dependencies=[Depends(get_current_client)],
)
safe_drive_africa_api_router.include_router(
    trips_router,
    prefix="/api",
    tags=["Trips"],
    dependencies=[Depends(require_roles(Role.ADMIN, Role.DRIVER))],
)
# safe_drive_africa_api_router.include_router(alcohol_questionnaire_router, prefix="/api", tags=["Alcohol Questionnaire"])
safe_drive_africa_api_router.include_router(
    alcohol_questionnaire_router,
    prefix="/api/alcohol-questionnaire",
    tags=["Alcohol Questionnaire"],
    dependencies=[Depends(require_roles(Role.ADMIN, Role.DRIVER))],
)

logger.info("Including alcohol_questionnaire_router in API router")
safe_drive_africa_api_router.include_router(
    alcohol_questionnaire_router,
    prefix="/api/alcohol_questionnaire",
    tags=["Alcohol Questionnaire"],
    dependencies=[Depends(require_roles(Role.ADMIN, Role.DRIVER))],
)
safe_drive_africa_api_router.include_router(
    alcohol_questionnaire_mobile_router,
    prefix="/api",
    tags=["Alcohol Questionnaire"],
    dependencies=[Depends(require_roles(Role.ADMIN, Role.DRIVER))],
)

safe_drive_africa_api_router.include_router(
    unsafe_behaviour_router,
    prefix="/api",
    tags=["Unsafe Behaviour"],
    dependencies=[Depends(require_roles(Role.ADMIN, Role.DRIVER))],
)
safe_drive_africa_api_router.include_router(
    raw_sensor_data_router,
    prefix="/api",
    tags=["Raw Sensor Data"],
    dependencies=[Depends(require_roles(Role.ADMIN, Role.DRIVER))],
)
safe_drive_africa_api_router.include_router(
    driver_profile_router,
    prefix="/api",
    tags=["Driver Profile"],
    dependencies=[Depends(require_roles(Role.ADMIN, Role.DRIVER))],
)
safe_drive_africa_api_router.include_router(
    driving_tips_router,
    prefix="/api",
    tags=["Driving Tips"],
    dependencies=[Depends(require_roles(Role.ADMIN, Role.DRIVER))],
)
safe_drive_africa_api_router.include_router(
    cause_router,
    prefix="/api",
    tags=["Cause"],
    dependencies=[Depends(require_roles(Role.ADMIN))],
)
safe_drive_africa_api_router.include_router(
    embedding_router,
    prefix="/api",
    tags=["Embedding"],
    dependencies=[Depends(require_roles(Role.ADMIN))],
)
safe_drive_africa_api_router.include_router(
    nlg_report_router,
    prefix="/api",
    tags=["NLG Report"],
    dependencies=[Depends(require_roles(Role.ADMIN, Role.DRIVER))],
)
safe_drive_africa_api_router.include_router(
    ai_model_inputs_router,
    prefix="/api",
    tags=["AI Model Inputs"],
    dependencies=[Depends(require_roles(Role.ADMIN, Role.DRIVER))],
)
safe_drive_africa_api_router.include_router(
    location_router,
    prefix="/api",
    tags=["Location"],
    dependencies=[Depends(require_roles(Role.ADMIN, Role.DRIVER))],
)
safe_drive_africa_api_router.include_router(
    behaviour_metrics_router,
    prefix="/api",
    tags=["Behaviour Metrics"],
    dependencies=[
        Depends(
            require_roles(
                Role.ADMIN,
                Role.RESEARCHER,
                Role.FLEET_MANAGER,
                Role.INSURANCE_PARTNER,
            )
        )
    ],
)
safe_drive_africa_api_router.include_router(
    fleet_monitoring_router,
    prefix="/api",
    tags=["Fleet Monitoring"],
    dependencies=[Depends(require_roles(Role.ADMIN, Role.FLEET_MANAGER))],
)
safe_drive_africa_api_router.include_router(
    fleet_management_router,
    prefix="/api",
    tags=["Fleet Management"],
    dependencies=[Depends(require_roles(Role.ADMIN, Role.FLEET_MANAGER))],
)
safe_drive_africa_api_router.include_router(
    researcher_router,
    prefix="/api",
    tags=["Researcher"],
    dependencies=[Depends(require_roles(Role.ADMIN, Role.RESEARCHER))],
)
safe_drive_africa_api_router.include_router(
    road_router,
    prefix="/api",
    tags=["Roads"],
    dependencies=[Depends(require_roles(Role.ADMIN))],
)
safe_drive_africa_api_router.include_router(
    insurance_partner_router,
    prefix="/api",
    tags=["Insurance Partner"],
    dependencies=[Depends(require_roles(Role.ADMIN, Role.INSURANCE_PARTNER))],
)
safe_drive_africa_api_router.include_router(
    admin_router,
    prefix="/api",
    tags=["Admin"],
    dependencies=[Depends(require_roles(Role.ADMIN))],
)
