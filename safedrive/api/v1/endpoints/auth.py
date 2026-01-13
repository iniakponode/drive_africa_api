from fastapi import APIRouter, Depends

from safedrive.core.security import ApiClientContext, get_current_client_or_driver
from safedrive.schemas.auth import AuthMeResponse

router = APIRouter()


@router.get("/auth/me", response_model=AuthMeResponse)
def get_auth_me(
    current_client: ApiClientContext = Depends(get_current_client_or_driver),
) -> AuthMeResponse:
    return AuthMeResponse(
        id=current_client.id,
        name=current_client.name,
        role=current_client.role.value,
        driverProfileId=current_client.driver_profile_id,
        fleet_id=current_client.fleet_id,
        insurance_partner_id=current_client.insurance_partner_id,
    )
