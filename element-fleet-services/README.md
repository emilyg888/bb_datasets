# Element Fleet Services Australia / Custom Fleet Synthetic Dataset

This folder contains synthetic datasets for an Australian fleet leasing and fleet-management operating model inspired by public information about Custom Fleet Australia and Element Fleet Management.

No row represents a real customer, driver, vehicle, vendor, claim, GPS point, invoice, or transaction. Names, IDs, amounts, dates, and operational outcomes are fabricated for analytics, prototyping, and data-model testing.

## Business Model Synthesis

Custom Fleet Australia presents itself as part of Element Fleet Management and as a fleet leasing and management provider for Australia and New Zealand. The public service model is a lifecycle fleet model:

- Finance and leasing: operating, finance, novated, and fully maintained lease options, with bundled services and residual/disposal management.
- Managed services: maintenance and tyres, fuel cards, registration and CTP, accident management, insurance support, roadside assistance, tolls/infringements, driver support, telematics, reporting, and client portals.
- Supplier network orchestration: repairers, maintenance providers, fuel partners, charging providers, auction/remarketing channels, and state registration/CTP processes.
- Data and technology: fleet analytics, driver app workflows, telematics, EV transition analysis, online claim updates, and client reporting.
- Revenue logic: lease financing/rental income plus service fees, rebills, transaction commissions, vendor network economics, telematics/technology fees, accident/insurance administration, and gains or proceeds from end-of-lease disposals.

## Public Sources Used

- Custom Fleet Australia home page: https://www.customfleet.com.au/
- Custom Fleet lease options: https://www.customfleet.com.au/lease/lease-options
- Custom Fleet accident management: https://www.customfleet.com.au/manage/accident-management
- Custom Fleet registration and CTP: https://www.customfleet.com.au/manage/registration-and-ctp
- Custom Fleet driver guide: https://www.customfleet.com.au/driver-support/index.html
- Custom Fleet EV program: https://www.customfleet.com.au/electric-vehicles/
- Element Fleet Management home page: https://www.elementfleet.com/
- Element 2025 financial results release: https://www.elementfleet.com/about/news/element-reports-fourth-quarter-and-record-2025-financial-results-raises-common-dividend-and-provides-full-year-2026-guidance
- Element 2024 Annual Information Form mirror: https://financialreports.eu/filings/element-fleet-management-corp/annual-report/2025/13771491/

Research was performed on 2026-05-26. The dataset is synthesized from the service categories and operating logic in those sources, not copied from source data.

## Files

| File | Rows | Business area |
| --- | ---: | --- |
| `clients.csv` | 18 | Shared client dimension |
| `vehicles.csv` | 150 | Shared vehicle dimension |
| `leasing_contracts.csv` | 150 | Leasing systems |
| `maintenance_vendors.csv` | 23 | Maintenance vendors |
| `maintenance_work_orders.csv` | 320 | Maintenance vendors / maintenance operations |
| `fuel_cards.csv` | 105 | Fuel card providers |
| `fuel_card_transactions.csv` | 559 | Fuel card providers |
| `telematics_daily.csv` | 1190 | Telematics / GPS |
| `insurance_claims.csv` | 85 | Insurance / accident claims |
| `vehicle_registration_events.csv` | 150 | Vehicle registration |
| `finance_billing_invoices.csv` | 240 | Finance / billing |
| `crm_client_portal_events.csv` | 420 | CRM / client portals |
| `driver_app_events.csv` | 520 | Driver apps |
| `ev_charging_sessions.csv` | 360 | EV charging data |
| `remarketing_auction_results.csv` | 65 | Remarketing / auction data |
| `metadata.json` | 1 | Dataset metadata |
| `generate_synthetic_data.py` | n/a | Reproducible generator |
| `delta_sources/2026-05-25/` | 96 | Day 1 synthetic mutable-source delta extracts |
| `delta_sources/2026-05-26/` | 96 | Day 2 synthetic mutable-source delta extracts |
| `generate_delta_sources.py` | n/a | Reproducible delta-source generator |
| `full_sources/2026-05-25/` | 4355 | Day 1 full daily source extracts |
| `full_sources/2026-05-26/` | 4355 | Day 2 full daily source extracts with cumulative changes |
| `full_sources/2026-05-27/` | 4355 | Day 3 full daily source extracts with cumulative changes |
| `full_sources/2026-05-28/` | 4355 | Day 4 full daily source extracts with cumulative changes |
| `generate_full_sources.py` | n/a | Reproducible full-source generator |

## Join Keys

- `client_id` joins all operating tables to `clients.csv`.
- `vehicle_id` joins all vehicle-level operating tables to `vehicles.csv`.
- `vendor_id` joins `maintenance_work_orders.csv` to `maintenance_vendors.csv`.
- `fuel_card_id` joins `fuel_card_transactions.csv` to `fuel_cards.csv`.

## Delta Source Files

Two days of synthetic source deltas are organized by extract date:

- `delta_sources/2026-05-25/`
- `delta_sources/2026-05-26/`

Each date folder contains update extracts for mutable source tables plus a `manifest.csv`. Delta files include the same columns as the base table, updated `effective_at` and `updated_at` values, and a `delta_action` column. Current delta actions are synthetic `UPDATE` rows only.

Immutable activity logs such as fuel-card transactions, telematics daily readings, and driver app events are excluded from these mutable-source deltas.

## Full Source Files

Two days of synthetic full source extracts are organized by extract date:

- `full_sources/2026-05-25/`
- `full_sources/2026-05-26/`
- `full_sources/2026-05-27/`
- `full_sources/2026-05-28/`

Each date folder contains all 15 source tables plus a `manifest.csv`. Mutable tables reflect the cumulative changes for that source date, while immutable activity logs are carried forward unchanged. The full-source manifests include `changed_from_previous_extract` to identify tables affected by that day's delta.

## Intended Uses

- Build fleet-management dashboards and KPI prototypes.
- Test data ingestion and schema mapping across leasing, maintenance, claims, billing, and telematics domains.
- Model end-to-end fleet lifecycle processes from vehicle order through service, driver interaction, EV charging, billing, and disposal.

Do not use this dataset for benchmarking Custom Fleet, Element Fleet, suppliers, accident rates, fuel economics, or vehicle residual values. The values are realistic-looking but intentionally synthetic.
