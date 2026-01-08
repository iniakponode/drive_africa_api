export type Role =
  | 'admin'
  | 'driver'
  | 'researcher'
  | 'fleet_manager'
  | 'insurance_partner'

export interface AuthMe {
  id: string
  name: string
  role: Role
  driverProfileId?: string | null
  fleet_id?: string | null
  insurance_partner_id?: string | null
}

export interface BulkActionResponse {
  created: number
  updated: number
  removed: number
  skipped: number
  errors: string[]
}

export interface LeaderboardEntry {
  driverProfileId: string
  ubpk: number
  unsafe_count: number
  distance_km: number
}

export interface LeaderboardResponse {
  period: string
  start_date: string
  end_date: string
  total_drivers: number
  best: LeaderboardEntry[]
  worst: LeaderboardEntry[]
}

export interface DriverKpi {
  driverProfileId: string
  ubpk: number
  unsafe_count: number
  distance_km: number
  bad_days: number
  bad_weeks: number
  bad_months: number
}

export interface DriverKpiResponse {
  period: string
  start_date: string
  end_date: string
  drivers: DriverKpi[]
}

export interface BadDaysThresholds {
  day: number
  week: number
  month: number
}

export interface BadDaysSummary {
  driverProfileId: string
  bad_days: number
  bad_weeks: number
  bad_months: number
  last_day_delta?: number | null
  last_week_delta?: number | null
  last_month_delta?: number | null
}

export interface BadDaysResponse {
  thresholds: BadDaysThresholds
  drivers: BadDaysSummary[]
}

export interface DriverPeriodUBPK {
  period_start: string
  period_end: string
  ubpk: number
  unsafe_count: number
  distance_km: number
}

export interface DriverUBPKSeriesResponse {
  driverProfileId: string
  period: string
  start_date: string
  end_date: string
  series: DriverPeriodUBPK[]
}

export interface FleetDriverMonitorIncident {
  id: string
  behaviour_type: string
  severity: number
  timestamp: number
}

export interface FleetDriverMonitor {
  driverProfileId: string
  activeTripStatus: string
  unsafeBehaviourCount: number
  unsafeBehaviourLast24h: number
  speedComplianceRatio: number
  speedingCount: number
  recentUnsafeBehaviours: FleetDriverMonitorIncident[]
}

export interface FleetDriverEvent {
  id: string
  driverProfileId: string
  event_type: string
  trip_id?: string | null
  message?: string | null
  gps_health?: string | null
  timestamp: string
}

export interface FleetDriverEventsResponse {
  events: FleetDriverEvent[]
}

export interface Fleet {
  id: string
  name: string
  description?: string | null
  region?: string | null
  created_at: string
}

export interface VehicleGroup {
  id: string
  name: string
  description?: string | null
  fleet_id: string
  created_at: string
}

export interface DriverFleetAssignment {
  id: string
  driverProfileId: string
  fleet_id: string
  vehicle_group_id?: string | null
  onboarding_completed?: boolean | null
  compliance_note?: string | null
  assigned_at: string
  fleet?: Fleet | null
  vehicle_group?: VehicleGroup | null
}

export interface AlcoholQuestionnaireSummary {
  id: string
  driverProfileId: string
  drankAlcohol: boolean
  plansToDrive: boolean
  impairmentLevel: number
  date?: string | null
}

export interface DriverAssignmentWithCompliance {
  assignment: DriverFleetAssignment
  questionnaire?: AlcoholQuestionnaireSummary | null
}

export interface FleetTripSummary {
  trip_id: string
  start_time?: string | null
  end_time?: string | null
  influence?: string | null
  distance_km: number
  unsafe_count: number
  avg_severity: number
  speeding_events: number
}

export interface FleetUnsafeBehaviourLog {
  id: string
  trip_id: string
  behaviour_type: string
  severity: number
  timestamp: number
}

export interface FleetAlcoholResponse {
  id: string
  drankAlcohol: boolean
  plansToDrive: boolean
  impairmentLevel: number
  date?: string | null
}

export interface FleetSpeedCompliance {
  total_records: number
  speeding_events: number
  compliance_ratio: number
}

export interface FleetReportResponse {
  driverProfileId: string
  report_generated_at: string
  trips: FleetTripSummary[]
  unsafe_behaviour_logs: FleetUnsafeBehaviourLog[]
  alcohol_responses: FleetAlcoholResponse[]
  speed_compliance: FleetSpeedCompliance
}

export interface FleetTripTip {
  tip_id: string
  title: string
  summary_tip?: string | null
  llm?: string | null
  date: string
}

export interface FleetTripSeverityFinding {
  id: string
  behaviour_type: string
  severity: number
  timestamp: number
}

export interface FleetTripNlgSummary {
  id: string
  report_text: string
  generated_at: string
}

export interface FleetTripContext {
  trip_id: string
  driverProfileId: string
  tips: FleetTripTip[]
  severity_findings: FleetTripSeverityFinding[]
  nlg_reports: FleetTripNlgSummary[]
}

export interface TripResponse {
  id: string
  driverProfileId: string
  start_date?: string | null
  end_date?: string | null
  start_time?: string | null
  startTime?: string | null
  end_time?: number | string | null
  sync?: boolean | null
  influence?: string | null
  trip_notes?: string | null
  tripNotes?: string | null
  alcohol_probability?: number | null
  alcoholProbability?: number | null
  user_alcohol_response?: string | null
  userAlcoholResponse?: string | null
}

export interface DrivingTip {
  tip_id: string
  title: string
  meaning?: string | null
  penalty?: string | null
  fine?: string | null
  law?: string | null
  hostility?: string | null
  summary_tip?: string | null
  sync: boolean
  date: string
  profile_id: string
  llm?: string | null
}

export interface NlgReport {
  id: string
  driverProfileId: string
  start_date?: string | null
  startDate?: string | null
  end_date?: string | null
  endDate?: string | null
  report_text: string
  generated_at: string
  sync: boolean
}

export interface UnsafeBehaviourSummary {
  behaviour_type: string
  total: number
  avg_severity: number
  min_severity: number
  max_severity: number
}

export interface RawSensorSummary {
  sensor_type: number
  sensor_type_name: string
  total: number
  min_timestamp?: number | null
  max_timestamp?: number | null
  avg_accuracy: number
}

export interface ResearcherDriverUbpk {
  driverProfileId: string
  ubpk: number
}

export interface ResearcherTripUbpk {
  trip_id: string
  driverProfileId: string
  ubpk: number
}

export interface AggregatedSnapshotResponse {
  generated_at: string
  ubpk_per_driver: ResearcherDriverUbpk[]
  ubpk_per_trip: ResearcherTripUbpk[]
  unsafe_behaviour_summary: UnsafeBehaviourSummary[]
  raw_sensor_summary: RawSensorSummary[]
}

export interface IngestionStatusItem {
  dataset: string
  total: number
  synced: number
  unsynced: number
  latest_record_at?: string | null
}

export interface IngestionStatusResponse {
  generated_at: string
  datasets: IngestionStatusItem[]
}

export interface ApiClient {
  id: string
  name: string
  role: Role
  active: boolean
  driverProfileId?: string | null
  fleet_id?: string | null
  insurance_partner_id?: string | null
  created_at: string
}

export interface ApiClientCreated extends ApiClient {
  api_key: string
}

export interface CloudEndpointConfig {
  road_limits_url?: string | null
  driving_tips_url?: string | null
  model_response_url?: string | null
}

export interface DatasetAccessConfig {
  datasets: Record<string, string[]>
}

export interface InsurancePartner {
  id: string
  name: string
  label: string
  active: boolean
  created_at: string
}

export interface InsurancePartnerDriver {
  id: string
  partner_id: string
  driverProfileId: string
  created_at: string
}

export interface DriverProfileResponse {
  driverProfileId: string
  email: string
  sync: boolean
}

export interface AlcoholQuestionnaire {
  id: string
  driverProfileId: string
  drankAlcohol: boolean
  selectedAlcoholTypes?: string | null
  beerQuantity?: string | null
  wineQuantity?: string | null
  spiritsQuantity?: string | null
  firstDrinkTime?: string | null
  lastDrinkTime?: string | null
  emptyStomach: boolean
  caffeinatedDrink: boolean
  impairmentLevel: number
  date: string
  plansToDrive: boolean
  sync: boolean
}

export interface ResearcherTripMetadata {
  id: string
  driverProfileId: string
  start_date?: string | null
  end_date?: string | null
  startTime?: number | string | null
  end_time?: number | string | null
  influence?: string | null
  tripNotes?: string | null
  alcoholProbability?: number | null
  userAlcoholResponse?: string | null
  matchedQuestionnaire?: AlcoholQuestionnaire | null
  sync?: boolean | null
}

export interface ResearcherTripAlcoholBundle {
  driverProfileId?: string | null
  start_date?: string | null
  end_date?: string | null
  matchingRule: string
  matchingTimezone: string
  total_trips: number
  total_questionnaires: number
  trips: ResearcherTripMetadata[]
  questionnaires: AlcoholQuestionnaire[]
}

export interface ResearcherBackfillResponse {
  driverProfileId?: string | null
  matchingRule: string
  matchingTimezone: string
  totalTrips: number
  matchedTrips: number
  updatedTrips: number
  skippedTripsNoDate: number
  overwrite: boolean
}

export interface InsuranceTelematicsTrip {
  trip_id: string
  driverProfileId: string
  start_time?: string | null
  end_time?: string | null
  influence?: string | null
  distance_km: number
  unsafe_count: number
  avg_severity: number
  speeding_events: number
  speed_compliance_ratio: number
}

export interface InsuranceTelematicsResponse {
  total: number
  trips: InsuranceTelematicsTrip[]
}

export interface InsuranceAlert {
  driverProfileId: string
  trip_id?: string | null
  alert_type: string
  severity?: number | null
  timestamp?: number | null
  message: string
}

export interface InsuranceAggregateDriverSummary {
  driverProfileId: string
  trip_count: number
  distance_km: number
  unsafe_count: number
  avg_severity: number
  speeding_events: number
  alcohol_positive: number
  latest_trip_start?: string | null
}

export interface InsuranceAggregateReport {
  generated_at: string
  partner_id?: string | null
  partner_label?: string | null
  start_date?: string | null
  end_date?: string | null
  total_drivers: number
  total_trips: number
  total_distance_km: number
  total_unsafe_events: number
  avg_unsafe_severity: number
  total_speeding_events: number
  alcohol_positive_responses: number
  drivers: InsuranceAggregateDriverSummary[]
}
