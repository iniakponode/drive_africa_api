from datetime import datetime, timedelta, timezone
from typing import Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field, root_validator, validator
from zoneinfo import ZoneInfo


def _parse_time_value(value: Any) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, datetime):
        return int(value.timestamp() * 1000)
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return None
        parsed_int = None
        try:
            parsed_int = int(raw)
        except ValueError:
            parsed_int = None
        if parsed_int is not None:
            return parsed_int
        try:
            return int(datetime.fromisoformat(raw.replace("Z", "+00:00")).timestamp() * 1000)
        except ValueError:
            return None
    return None


def _format_local_time(
    epoch_ms: Optional[int],
    tz_id: Optional[str],
    tz_offset_minutes: Optional[int],
) -> Optional[str]:
    if epoch_ms is None:
        return None
    if tz_id:
        try:
            zone = ZoneInfo(tz_id)
            return datetime.fromtimestamp(epoch_ms / 1000, tz=zone).isoformat()
        except Exception:
            pass
    if tz_offset_minutes is not None:
        offset = timezone(timedelta(minutes=tz_offset_minutes))
        return datetime.fromtimestamp(epoch_ms / 1000, tz=offset).isoformat()
    return datetime.fromtimestamp(epoch_ms / 1000, tz=timezone.utc).isoformat()


class TripCreatePayload(BaseModel):
    id: UUID
    driverProfileId: Optional[UUID] = Field(default=None, alias="driver_profile_id")
    startDate: Optional[datetime] = Field(default=None, alias="start_date")
    endDate: Optional[datetime] = Field(default=None, alias="end_date")
    startTime: Optional[int] = Field(default=None, alias="start_time")
    endTime: Optional[int] = Field(default=None, alias="end_time")
    timeZoneId: Optional[str] = Field(default=None, alias="time_zone_id")
    timeZoneOffsetMinutes: Optional[int] = Field(default=None, alias="time_zone_offset_minutes")
    sync: bool = True
    influence: Optional[str] = None
    userAlcoholResponse: Optional[str] = Field(default=None, alias="user_alcohol_response")
    alcoholProbability: Optional[float] = Field(default=None, alias="alcohol_probability")
    notes: Optional[str] = None

    @validator("startTime", "endTime", pre=True)
    def parse_time_fields(cls, value: Any) -> Optional[int]:
        return _parse_time_value(value)

    @root_validator(skip_on_failure=True)
    def normalize_time_fields(cls, values: dict) -> dict:
        start_time = values.get("startTime")
        end_time = values.get("endTime")
        start_date = values.get("startDate")
        end_date = values.get("endDate")
        if start_time is None and start_date is not None:
            values["startTime"] = int(start_date.timestamp() * 1000)
        elif start_time is not None and start_time < 10_000_000_000 and start_date is not None:
            values["startTime"] = int(start_date.timestamp() * 1000)
        elif start_time is not None and 1_000_000_000 <= start_time < 10_000_000_000 and start_date is None:
            values["startTime"] = start_time * 1000

        if end_time is None and end_date is not None:
            values["endTime"] = int(end_date.timestamp() * 1000)
        elif end_time is not None and end_time < 10_000_000_000 and end_date is not None:
            values["endTime"] = int(end_date.timestamp() * 1000)
        elif end_time is not None and 1_000_000_000 <= end_time < 10_000_000_000 and end_date is None:
            values["endTime"] = end_time * 1000
        return values

    class Config:
        orm_mode = True
        extra = "ignore"
        allow_population_by_field_name = True
        allow_population_by_alias = True


class TripResponsePayload(BaseModel):
    id: UUID
    driverProfileId: UUID
    startDate: Optional[datetime] = None
    endDate: Optional[datetime] = None
    startTime: Optional[int] = None
    endTime: Optional[int] = None
    startTimeLocal: Optional[str] = None
    endTimeLocal: Optional[str] = None
    timeZoneId: Optional[str] = None
    timeZoneOffsetMinutes: Optional[int] = None
    sync: bool
    influence: Optional[str] = None
    userAlcoholResponse: Optional[str] = None
    alcoholProbability: Optional[float] = None
    notes: Optional[str] = None

    class Config:
        orm_mode = True
