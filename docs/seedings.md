# Seeded Data (MySQL drive_safe_db)

Last Updated: 2026-01-09

## Seeding Scripts

### Basic Seeding (Admin & Researcher only)
```bash
cd /var/www/vhosts/safedriveafrica.com/api.safedriveafrica.com
source venv/bin/activate
python scripts/seed_api_keys.py
```

### Advanced Seeding (Uses existing data)
Creates API keys for existing fleets, drivers, and insurance partners:
```bash
python scripts/seed_with_existing_data.py
```

---

## Previous Seed Data

Date: 2026-01-06

## Dataset Access
Default dataset access policy stored under `admin_setting.key = dataset_access`:

```json
{
  "datasets": {
    "researcher_unsafe_behaviours": ["admin", "researcher"],
    "researcher_raw_sensor_data": ["admin", "researcher"],
    "researcher_alcohol_trip_bundle": ["admin", "researcher"],
    "researcher_nlg_reports": ["admin", "researcher"],
    "researcher_raw_sensor_export": ["admin", "researcher"],
    "researcher_trips_export": ["admin", "researcher"],
    "researcher_aggregate_snapshot": ["admin", "researcher"],
    "researcher_ingestion_status": ["admin", "researcher"],
    "behaviour_metrics": ["admin", "researcher", "fleet_manager", "insurance_partner"],
    "fleet_monitoring": ["admin", "fleet_manager"],
    "fleet_assignments": ["admin", "fleet_manager"],
    "fleet_events": ["admin", "fleet_manager"],
    "fleet_trip_context": ["admin", "fleet_manager"],
    "fleet_reports": ["admin", "fleet_manager"],
    "insurance_telematics": ["admin", "insurance_partner"],
    "insurance_reports": ["admin", "insurance_partner"],
    "insurance_raw_sensor_export": ["admin", "insurance_partner"],
    "insurance_alerts": ["admin", "insurance_partner"],
    "insurance_aggregate_reports": ["admin", "insurance_partner"]
  }
}
```

## Fleets and Vehicle Groups
- Fleet `Abuja Ops` (id `af1fbd02-6ffd-4917-ae98-58ea1b661efc`, region `Abuja`, desc `None`); vehicle groups: `VIP` (id `8bfd2ab4-45ee-4936-aa8d-f6cbca8204e1`, desc `Executive`).
- Fleet `Lagos Ops` (id `5564e348-99dc-4921-858e-d06887d33077`, region `Lagos`, desc `Main ops`); vehicle groups: `Route A` (id `b10ae80c-4ce1-4060-a358-7d01c56b3a8b`, desc `Daily pickups`), `Route B` (id `37ddb8cd-90d7-4d76-a8bd-935b75778d92`, desc `Long haul`).

## Insurance Partners
- Insurance partner `Merit` (id `7cbe492d-39be-4a66-9069-7e5833d62f35`, label `merit`, active `True`).

## API Clients (keys stored for testing)
- `Ayibatonbrapa` (admin) id `bb33af69-a843-487c-bc53-5fd3dd22febb`.
- `Angel` (researcher) id `9c7323df-0dfd-4929-b769-1da0e8788550`.
- `Princess` (fleet_manager) id `908600d2-3d0b-49c7-8bb8-a770171716fa`, fleet_id `5564e348-99dc-4921-858e-d06887d33077`.
- `Merit` (insurance_partner) id `a59480a1-3ac5-46df-9830-8f00554e2212`, insurance_partner_id `7cbe492d-39be-4a66-9069-7e5833d62f35`.
- `Elon` (driver) id `5ca5c4e1-5adb-4755-a609-fc13f5e59a2c`, driverProfileId `e1c3446f-ffbc-4b90-b5be-2d8d25869d31`.
- `Iniakpokeikiye` (driver) id `8451137d-9bbe-4534-8358-1a89bf0aa23c`, driverProfileId `3fe59d68-08d1-4b09-9799-9ad0741562f4`.

### API Keys
- `Ayibatonbrapa` (admin): `FeZGph0Os2oPHofcpgp0NlYODfdzwDSIErBC_105uVs`
- `Angel` (researcher): `_USjfodeUHhJe6TRktpV61Q8o3yQyCfrobmWK4eyyJE`
- `Princess` (fleet_manager): `7daCkNFRVA4Mv0tBCXbvljiLeddGP3sC5efdt4gV5T4`
- `Merit` (insurance_partner): `pNO7a83DOSaNqq2cHZG8WtpL87Vr5JdPHTPitnshqyY`
- `Elon` (driver): `LXipOA9o0WLlqah0rIiIa4zyfQX7rURfCLE2k-sjMW8`
- `Iniakpokeikiye` (driver): `Fmxl230RwokpaIbqE9RyvHD7RCdi9EVs_DZIgSgnmhA`

## Driver Profiles
- `driver.elon.3d31e2@safedrive.local` (driverProfileId `e1c3446f-ffbc-4b90-b5be-2d8d25869d31`, sync `False`).
- `driver.iniakpokeikiye.02bbac@safedrive.local` (driverProfileId `3fe59d68-08d1-4b09-9799-9ad0741562f4`, sync `False`).

## Fleet Assignments
- Assignment `207eb37a-faa3-48c5-9ca7-f0128d6f4e23`: driver `e1c3446f-ffbc-4b90-b5be-2d8d25869d31` -> fleet `5564e348-99dc-4921-858e-d06887d33077`, vehicle_group `b10ae80c-4ce1-4060-a358-7d01c56b3a8b`.
- Assignment `c285a7b6-ec70-4b3b-ab3e-cb4ccacd116e`: driver `3fe59d68-08d1-4b09-9799-9ad0741562f4` -> fleet `5564e348-99dc-4921-858e-d06887d33077`, vehicle_group `37ddb8cd-90d7-4d76-a8bd-935b75778d92`.

## Insurance Partner Driver Mapping
- Mapping `cc7cf11c-a538-4db0-a2b1-efdb20bf722e`: partner `7cbe492d-39be-4a66-9069-7e5833d62f35` -> driver `e1c3446f-ffbc-4b90-b5be-2d8d25869d31`.
- Mapping `44860807-4706-40e1-a7e8-955ae6e1090c`: partner `7cbe492d-39be-4a66-9069-7e5833d62f35` -> driver `3fe59d68-08d1-4b09-9799-9ad0741562f4`.
