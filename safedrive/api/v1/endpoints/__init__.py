# from fastapi import APIRouter
# from safedrive.api.v1.endpoints.trip import router as trips_router
# from safedrive.api.v1.endpoints.index import router as index_router
# from safedrive.api.v1.endpoints.unsafe_behaviour import router as unsafe_behaviour_router
# from safedrive.api.v1.endpoints.raw_sensor_data import router as raw_sensor_data_router
# from safedrive.api.v1.endpoints.driver_profile import router as driver_profile_router
# from safedrive.api.v1.endpoints.driving_tips import router as driving_tips_router
# from safedrive.api.v1.endpoints.cause import router as cause_router
# from safedrive.api.v1.endpoints.embedding import router as embedding_router
# from safedrive.api.v1.endpoints.nlg_report import router as nlg_report_router
# from safedrive.api.v1.endpoints.ai_model_inputs_router import router as ai_model_inputs_router
# from safedrive.api.v1.endpoints.index import router as index_router
# from safedrive.api.v1.endpoints.location import router as location_router
# from safedrive import safe_drive_africa_api_router as safe_drive_africa_api_router

# safe_drive_africa_api_router.include_router(index_router, prefix="/api", tags=["Index"])
# safe_drive_africa_api_router.include_router(trips_router, prefix="/api", tags=["Trips"])
# safe_drive_africa_api_router.include_router(unsafe_behaviour_router, prefix="/api", tags=["Unsafe Behaviour"])
# safe_drive_africa_api_router.include_router(raw_sensor_data_router, prefix="/api", tags=["Raw Sensor Data"])
# safe_drive_africa_api_router.include_router(driver_profile_router, prefix="/api", tags=["Driver Profile"])
# safe_drive_africa_api_router.include_router(driving_tips_router, prefix="/api", tags=["Driving Tips"])
# safe_drive_africa_api_router.include_router(cause_router, prefix="/api", tags=["Cause"])
# safe_drive_africa_api_router.include_router(embedding_router, prefix="/api", tags=["Embedding"])
# safe_drive_africa_api_router.include_router(nlg_report_router, prefix="/api", tags=["NLG Report"])
# safe_drive_africa_api_router.include_router(ai_model_inputs_router, prefix="/api", tags=["AI Model Inputs"])
# safe_drive_africa_api_router.include_router(location_router, prefix="/api", tags=["Location"])