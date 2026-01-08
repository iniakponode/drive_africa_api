import type {
  AuthMe,
  BadDaysResponse,
  DriverKpiResponse,
  DriverUBPKSeriesResponse,
  DrivingTip,
  FleetDriverEventsResponse,
  FleetDriverMonitor,
  FleetReportResponse,
  DriverAssignmentWithCompliance,
  InsuranceAlert,
  InsuranceAggregateReport,
  InsuranceTelematicsResponse,
  LeaderboardResponse,
  NlgReport,
  TripResponse,
  UnsafeBehaviourSummary,
  RawSensorSummary,
  AggregatedSnapshotResponse,
  IngestionStatusResponse,
  ApiClient,
  ApiClientCreated,
  CloudEndpointConfig,
  DatasetAccessConfig,
  InsurancePartner,
  InsurancePartnerDriver,
  DriverProfileResponse,
  FleetTripContext,
  Fleet,
  VehicleGroup,
  AlcoholQuestionnaire,
  ResearcherTripAlcoholBundle,
  ResearcherBackfillResponse,
  BulkActionResponse,
} from './types'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ''

type ScopeParams = {
  fleetId?: string
  insurancePartnerId?: string
}

function scopeQuery(scope?: ScopeParams) {
  if (!scope) {
    return ''
  }
  const params = new URLSearchParams()
  if (scope.fleetId) {
    params.set('fleetId', scope.fleetId)
  }
  if (scope.insurancePartnerId) {
    params.set('insurancePartnerId', scope.insurancePartnerId)
  }
  const query = params.toString()
  return query ? `&${query}` : ''
}

function scopeQueryPrefix(scope?: ScopeParams) {
  if (!scope) {
    return ''
  }
  const params = new URLSearchParams()
  if (scope.fleetId) {
    params.set('fleetId', scope.fleetId)
  }
  if (scope.insurancePartnerId) {
    params.set('insurancePartnerId', scope.insurancePartnerId)
  }
  const query = params.toString()
  return query ? `?${query}` : ''
}

type QueryParams = Record<
  string,
  string | number | boolean | undefined | null
>

function buildQuery(params: QueryParams) {
  const search = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === '') {
      return
    }
    search.set(key, String(value))
  })
  return search.toString()
}

export async function apiFetch<T>(
  path: string,
  apiKey: string,
  options: RequestInit = {},
): Promise<T> {
  const url = API_BASE ? `${API_BASE}${path}` : path
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': apiKey,
      ...(options.headers ?? {}),
    },
  })
  if (!response.ok) {
    const message = await response.text()
    throw new Error(message || `Request failed: ${response.status}`)
  }
  return (await response.json()) as T
}

export async function apiFetchBlob(
  path: string,
  apiKey: string,
  options: RequestInit = {},
): Promise<Blob> {
  const url = API_BASE ? `${API_BASE}${path}` : path
  const response = await fetch(url, {
    ...options,
    headers: {
      'X-API-Key': apiKey,
      ...(options.headers ?? {}),
    },
  })
  if (!response.ok) {
    const message = await response.text()
    throw new Error(message || `Request failed: ${response.status}`)
  }
  return response.blob()
}

export function getAuthMe(apiKey: string): Promise<AuthMe> {
  return apiFetch<AuthMe>('/api/auth/me', apiKey)
}

export function getLeaderboard(
  apiKey: string,
  period: string,
  scope?: ScopeParams,
): Promise<LeaderboardResponse> {
  return apiFetch<LeaderboardResponse>(
    `/api/analytics/leaderboard?period=${encodeURIComponent(period)}${scopeQuery(
      scope,
    )}`,
    apiKey,
  )
}

export function getDriverKpis(
  apiKey: string,
  period: string,
  scope?: ScopeParams,
): Promise<DriverKpiResponse> {
  return apiFetch<DriverKpiResponse>(
    `/api/analytics/driver-kpis?period=${encodeURIComponent(period)}${scopeQuery(
      scope,
    )}`,
    apiKey,
  )
}

export function getBadDays(
  apiKey: string,
  scope?: ScopeParams,
): Promise<BadDaysResponse> {
  return apiFetch<BadDaysResponse>(
    `/api/analytics/bad-days${scopeQueryPrefix(scope)}`,
    apiKey,
  )
}

export function getDriverUbpkSeries(
  apiKey: string,
  period: string,
  driverProfileId?: string,
): Promise<DriverUBPKSeriesResponse> {
  const params = new URLSearchParams({ period })
  if (driverProfileId) {
    params.set('driverProfileId', driverProfileId)
  }
  return apiFetch<DriverUBPKSeriesResponse>(
    `/api/analytics/driver-ubpk?${params.toString()}`,
    apiKey,
  )
}

export function getFleetDriverMonitor(
  apiKey: string,
  driverProfileId: string,
): Promise<FleetDriverMonitor> {
  return apiFetch<FleetDriverMonitor>(
    `/api/fleet/driver_monitor/${driverProfileId}`,
    apiKey,
  )
}

export function getFleetDriverEvents(
  apiKey: string,
  driverProfileId: string,
  limit = 20,
): Promise<FleetDriverEventsResponse> {
  const query = buildQuery({ limit })
  return apiFetch<FleetDriverEventsResponse>(
    `/api/fleet/events/${driverProfileId}?${query}`,
    apiKey,
  )
}

export function getFleetAssignment(
  apiKey: string,
  driverProfileId: string,
): Promise<DriverAssignmentWithCompliance> {
  return apiFetch<DriverAssignmentWithCompliance>(
    `/api/fleet/assignments/${driverProfileId}`,
    apiKey,
  )
}

export function getFleetReport(
  apiKey: string,
  driverProfileId: string,
): Promise<FleetReportResponse> {
  return apiFetch<FleetReportResponse>(
    `/api/fleet/reports/${driverProfileId}`,
    apiKey,
  )
}

export function getTrips(
  apiKey: string,
  params: { skip?: number; limit?: number } = {},
): Promise<TripResponse[]> {
  const query = buildQuery(params)
  const suffix = query ? `?${query}` : ''
  return apiFetch<TripResponse[]>(`/api/trips/${suffix}`, apiKey)
}

export function getDrivingTips(
  apiKey: string,
  params: {
    skip?: number
    limit?: number
    profile_id?: string
    llm?: string
    start_date?: string
    end_date?: string
    sync?: boolean
  } = {},
): Promise<DrivingTip[]> {
  const query = buildQuery(params)
  const suffix = query ? `?${query}` : ''
  return apiFetch<DrivingTip[]>(`/api/driving_tips/${suffix}`, apiKey)
}

export function getNlgReports(
  apiKey: string,
  params: {
    skip?: number
    limit?: number
    driverProfileId?: string
    startDate?: string
    endDate?: string
    sync?: boolean
  } = {},
): Promise<NlgReport[]> {
  const query = buildQuery(params)
  const suffix = query ? `?${query}` : ''
  return apiFetch<NlgReport[]>(`/api/nlg_reports/${suffix}`, apiKey)
}

export function getResearcherUnsafeSummary(
  apiKey: string,
  params: {
    driverProfileId?: string
    tripId?: string
    startDate?: string
    endDate?: string
    week?: string
    minSeverity?: number
    maxSeverity?: number
  } = {},
): Promise<UnsafeBehaviourSummary[]> {
  const query = buildQuery(params)
  const suffix = query ? `?${query}` : ''
  return apiFetch<UnsafeBehaviourSummary[]>(
    `/api/researcher/unsafe_behaviours/summary${suffix}`,
    apiKey,
  )
}

export function getResearcherRawSensorSummary(
  apiKey: string,
  params: {
    driverProfileId?: string
    tripId?: string
    sensorType?: number
    sensorTypeName?: string
    startTimestamp?: number
    endTimestamp?: number
    startDate?: string
    endDate?: string
    week?: string
  } = {},
): Promise<RawSensorSummary[]> {
  const query = buildQuery(params)
  const suffix = query ? `?${query}` : ''
  return apiFetch<RawSensorSummary[]>(
    `/api/researcher/raw_sensor_data/summary${suffix}`,
    apiKey,
  )
}

export function getResearcherAggregateSnapshot(
  apiKey: string,
  params: {
    driverProfileId?: string
    startDate?: string
    endDate?: string
    week?: string
  } = {},
): Promise<AggregatedSnapshotResponse> {
  const query = buildQuery(params)
  const suffix = query ? `?${query}` : ''
  return apiFetch<AggregatedSnapshotResponse>(
    `/api/researcher/snapshots/aggregate${suffix}`,
    apiKey,
  )
}

export function getResearcherIngestionStatus(
  apiKey: string,
): Promise<IngestionStatusResponse> {
  return apiFetch<IngestionStatusResponse>(
    '/api/researcher/ingestion/status',
    apiKey,
  )
}

export function getInsuranceTelematicsTrips(
  apiKey: string,
  params: {
    driverProfileId?: string
    startDate?: string
    endDate?: string
    skip?: number
    limit?: number
  } = {},
): Promise<InsuranceTelematicsResponse> {
  const query = buildQuery(params)
  const suffix = query ? `?${query}` : ''
  return apiFetch<InsuranceTelematicsResponse>(
    `/api/insurance/telematics/trips${suffix}`,
    apiKey,
  )
}

export function getInsuranceAlerts(
  apiKey: string,
  params: {
    minSeverity?: number
    sinceHours?: number
    limit?: number
  } = {},
): Promise<InsuranceAlert[]> {
  const query = buildQuery(params)
  const suffix = query ? `?${query}` : ''
  return apiFetch<InsuranceAlert[]>(
    `/api/insurance/alerts${suffix}`,
    apiKey,
  )
}

export function getInsuranceAggregateReport(
  apiKey: string,
  params: {
    partnerId?: string
    partnerLabel?: string
    startDate?: string
    endDate?: string
  } = {},
): Promise<InsuranceAggregateReport> {
  const query = buildQuery(params)
  const suffix = query ? `?${query}` : ''
  return apiFetch<InsuranceAggregateReport>(
    `/api/insurance/reports/aggregate${suffix}`,
    apiKey,
  )
}

export function getInsuranceDriverReport(
  apiKey: string,
  driverId: string,
): Promise<FleetReportResponse> {
  return apiFetch<FleetReportResponse>(
    `/api/insurance/reports/${driverId}`,
    apiKey,
  )
}

export function getApiClients(apiKey: string): Promise<ApiClient[]> {
  return apiFetch<ApiClient[]>('/api/admin/api-clients/', apiKey)
}

export function createApiClient(
  apiKey: string,
  payload: {
    name: string
    role: string
    active?: boolean
    driverProfileId?: string
    fleet_id?: string
    insurance_partner_id?: string
    api_key?: string
  },
): Promise<ApiClientCreated> {
  return apiFetch<ApiClientCreated>('/api/admin/api-clients/', apiKey, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function batchCreateApiClients(
  apiKey: string,
  payload: Array<{
    name: string
    role: string
    active?: boolean
    driverProfileId?: string
    fleet_id?: string
    insurance_partner_id?: string
    api_key?: string
  }>,
): Promise<BulkActionResponse> {
  return apiFetch<BulkActionResponse>('/api/admin/api_clients/batch_create', apiKey, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function updateApiClient(
  apiKey: string,
  clientId: string,
  payload: {
    name?: string
    role?: string
    active?: boolean
    driverProfileId?: string | null
    fleet_id?: string | null
    insurance_partner_id?: string | null
  },
): Promise<ApiClient> {
  return apiFetch<ApiClient>(`/api/admin/api-clients/${clientId}`, apiKey, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export function getDatasetAccess(
  apiKey: string,
): Promise<DatasetAccessConfig> {
  return apiFetch<DatasetAccessConfig>('/api/admin/dataset-access', apiKey)
}

export function updateDatasetAccess(
  apiKey: string,
  payload: DatasetAccessConfig,
): Promise<DatasetAccessConfig> {
  return apiFetch<DatasetAccessConfig>('/api/admin/dataset-access', apiKey, {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
}

export function getCloudEndpoints(
  apiKey: string,
): Promise<CloudEndpointConfig> {
  return apiFetch<CloudEndpointConfig>('/api/admin/cloud-endpoints', apiKey)
}

export function updateCloudEndpoints(
  apiKey: string,
  payload: CloudEndpointConfig,
): Promise<CloudEndpointConfig> {
  return apiFetch<CloudEndpointConfig>('/api/admin/cloud-endpoints', apiKey, {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
}

export function getInsurancePartners(
  apiKey: string,
): Promise<InsurancePartner[]> {
  return apiFetch<InsurancePartner[]>('/api/admin/insurance-partners/', apiKey)
}

export function createInsurancePartner(
  apiKey: string,
  payload: {
    name: string
    label: string
    active?: boolean
  },
): Promise<InsurancePartner> {
  return apiFetch<InsurancePartner>('/api/admin/insurance-partners/', apiKey, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function assignInsurancePartnerDriver(
  apiKey: string,
  partnerId: string,
  driverProfileId: string,
): Promise<InsurancePartnerDriver> {
  return apiFetch<InsurancePartnerDriver>(
    `/api/admin/insurance-partners/${partnerId}/drivers`,
    apiKey,
    {
      method: 'POST',
      body: JSON.stringify({ driverProfileId }),
    },
  )
}

export function removeInsurancePartnerDriver(
  apiKey: string,
  partnerId: string,
  driverProfileId: string,
): Promise<void> {
  return apiFetch<void>(
    `/api/admin/insurance-partners/${partnerId}/drivers/${driverProfileId}`,
    apiKey,
    { method: 'DELETE' },
  )
}

export function batchAssignInsurancePartnerMappings(
  apiKey: string,
  payload: Array<{ partner_id: string; driverProfileId: string }>,
): Promise<BulkActionResponse> {
  return apiFetch<BulkActionResponse>(
    '/api/admin/insurance_partner_mappings/batch_assign',
    apiKey,
    {
      method: 'POST',
      body: JSON.stringify(payload),
    },
  )
}

export function batchRemoveInsurancePartnerMappings(
  apiKey: string,
  payload: Array<{ partner_id: string; driverProfileId: string }>,
): Promise<BulkActionResponse> {
  return apiFetch<BulkActionResponse>(
    '/api/admin/insurance_partner_mappings/batch_remove',
    apiKey,
    {
      method: 'DELETE',
      body: JSON.stringify(payload),
    },
  )
}

export function getDriverProfiles(
  apiKey: string,
  params: { skip?: number; limit?: number } = {},
): Promise<DriverProfileResponse[]> {
  const query = buildQuery(params)
  const suffix = query ? `?${query}` : ''
  return apiFetch<DriverProfileResponse[]>(
    `/api/driver_profiles/${suffix}`,
    apiKey,
  )
}

export function createDriverProfile(
  apiKey: string,
  payload: {
    driverProfileId: string
    email: string
    sync?: boolean
  },
): Promise<DriverProfileResponse> {
  return apiFetch<DriverProfileResponse>('/api/driver_profiles/', apiKey, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function updateDriverProfile(
  apiKey: string,
  profileId: string,
  payload: { email?: string; sync?: boolean },
): Promise<DriverProfileResponse> {
  return apiFetch<DriverProfileResponse>(
    `/api/driver_profiles/${profileId}`,
    apiKey,
    {
      method: 'PUT',
      body: JSON.stringify(payload),
    },
  )
}

export function getDriverProfile(
  apiKey: string,
  profileId: string,
): Promise<DriverProfileResponse> {
  return apiFetch<DriverProfileResponse>(
    `/api/driver_profiles/${profileId}`,
    apiKey,
  )
}

export function getFleetTripContext(
  apiKey: string,
  tripId: string,
): Promise<FleetTripContext> {
  return apiFetch<FleetTripContext>(
    `/api/fleet/trips/${tripId}/context`,
    apiKey,
  )
}

export function getFleets(apiKey: string): Promise<Fleet[]> {
  return apiFetch<Fleet[]>('/api/fleet/', apiKey)
}

export function createFleet(
  apiKey: string,
  payload: { name: string; description?: string; region?: string },
): Promise<Fleet> {
  return apiFetch<Fleet>('/api/fleet/', apiKey, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function getFleetVehicleGroups(
  apiKey: string,
  fleetId: string,
): Promise<VehicleGroup[]> {
  return apiFetch<VehicleGroup[]>(
    `/api/fleet/${fleetId}/vehicle-groups`,
    apiKey,
  )
}

export function batchCreateFleetVehicleGroups(
  apiKey: string,
  payload: Array<{ fleet_id: string; name: string; description?: string }>,
): Promise<BulkActionResponse> {
  return apiFetch<BulkActionResponse>('/api/fleet/vehicle_groups/batch_create', apiKey, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function batchUpdateFleetVehicleGroups(
  apiKey: string,
  payload: Array<{ group_id: string; name?: string; description?: string }>,
): Promise<BulkActionResponse> {
  return apiFetch<BulkActionResponse>('/api/fleet/vehicle_groups/batch_update', apiKey, {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
}

export function createFleetVehicleGroup(
  apiKey: string,
  fleetId: string,
  payload: { name: string; description?: string },
): Promise<VehicleGroup> {
  return apiFetch<VehicleGroup>(
    `/api/fleet/${fleetId}/vehicle-groups`,
    apiKey,
    {
      method: 'POST',
      body: JSON.stringify(payload),
    },
  )
}

export function updateFleetVehicleGroup(
  apiKey: string,
  groupId: string,
  payload: { name?: string; description?: string },
): Promise<VehicleGroup> {
  return apiFetch<VehicleGroup>(
    `/api/fleet/vehicle-groups/${groupId}`,
    apiKey,
    {
      method: 'PATCH',
      body: JSON.stringify(payload),
    },
  )
}

export function batchCreateDriverProfiles(
  apiKey: string,
  payload: Array<{ driverProfileId: string; email: string; sync?: boolean }>,
): Promise<BulkActionResponse> {
  return apiFetch<BulkActionResponse>(
    '/api/driver_profiles/batch_create',
    apiKey,
    {
      method: 'POST',
      body: JSON.stringify(payload),
    },
  )
}

export function getAlcoholQuestionnaires(
  apiKey: string,
): Promise<AlcoholQuestionnaire[]> {
  return apiFetch<AlcoholQuestionnaire[]>(
    '/api/alcohol-questionnaire/questionnaire/',
    apiKey,
  )
}

export function createAlcoholQuestionnaire(
  apiKey: string,
  payload: AlcoholQuestionnaire,
): Promise<AlcoholQuestionnaire> {
  return apiFetch<AlcoholQuestionnaire>(
    '/api/alcohol-questionnaire/questionnaire/',
    apiKey,
    {
      method: 'POST',
      body: JSON.stringify(payload),
    },
  )
}

export function updateTrip(
  apiKey: string,
  tripId: string,
  payload: {
    tripNotes?: string
    influence?: string
    userAlcoholResponse?: string
    alcoholProbability?: number
  },
): Promise<TripResponse> {
  return apiFetch<TripResponse>(`/api/trips/${tripId}`, apiKey, {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
}

export function getResearcherAlcoholBundle(
  apiKey: string,
  params: {
    driverProfileId?: string
    startDate?: string
    endDate?: string
    week?: string
    skip?: number
    limit?: number
  } = {},
): Promise<ResearcherTripAlcoholBundle> {
  const query = buildQuery(params)
  const suffix = query ? `?${query}` : ''
  return apiFetch<ResearcherTripAlcoholBundle>(
    `/api/researcher/alcohol_trip_bundle${suffix}`,
    apiKey,
  )
}

export function backfillTripAlcohol(
  apiKey: string,
  params: {
    driverProfileId?: string
    startDate?: string
    endDate?: string
    week?: string
    overwrite?: boolean
  } = {},
): Promise<ResearcherBackfillResponse> {
  const query = buildQuery(params)
  const suffix = query ? `?${query}` : ''
  return apiFetch<ResearcherBackfillResponse>(
    `/api/researcher/trips/backfill_alcohol${suffix}`,
    apiKey,
    {
      method: 'POST',
    },
  )
}
