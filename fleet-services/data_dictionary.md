# Data Dictionary

All tables are synthetic and use stable IDs suitable for joins.

## Source Control Columns

Mutable entity and workflow tables include these required future source columns:

- `effective_at`: Timestamp when the source-system record version became business-effective.
- `updated_at`: Timestamp when the source-system record version was last updated.

These columns are present in `clients.csv`, `vehicles.csv`, `leasing_contracts.csv`, `maintenance_vendors.csv`, `maintenance_work_orders.csv`, `fuel_cards.csv`, `insurance_claims.csv`, `vehicle_registration_events.csv`, `finance_billing_invoices.csv`, `crm_client_portal_events.csv`, `ev_charging_sessions.csv`, and `remarketing_auction_results.csv`.

They are intentionally not included in immutable activity logs: `fuel_card_transactions.csv`, `telematics_daily.csv`, and `driver_app_events.csv`.

## Delta Source Extracts

The `delta_sources/YYYY-MM-DD/` folders contain daily update extracts for mutable tables. Each date folder includes:

- `manifest.csv`: table-level row counts for that source date.
- One CSV per mutable table listed above.

Delta files retain the base table columns and add:

- `delta_action`: Change operation represented by the row. Current synthetic extracts use `UPDATE`.

## Full Source Extracts

The `full_sources/YYYY-MM-DD/` folders contain daily full extracts for `2026-05-25` through `2026-05-28`. Each date folder includes:

- `manifest.csv`: table-level row counts and a `changed_from_previous_extract` flag.
- All 15 source CSV tables.

Full extracts do not add `delta_action`; they retain the base table schema. Mutable tables contain cumulative changes through the source date.

## Shared Dimensions

### `clients.csv`
- `client_id`: Synthetic client identifier.
- `abn`: Synthetic Australian Business Number-style identifier.
- `client_name`: Fabricated customer name.
- `industry_segment`: Broad customer industry.
- `email_domain`: Synthetic client email domain.
- `address_line_1`, `suburb`, `state`, `postcode`, `country`: Synthetic client address fields.
- `headquarters_state`: Australian state or territory.
- `fleet_size_band`: Approximate fleet size band.
- `contract_start_date`: Synthetic client contract start date.
- `client_status`: Lifecycle state for the client relationship.
- `effective_at`, `updated_at`: Required source control timestamps.

### `vehicles.csv`
- `vehicle_id`: Synthetic vehicle identifier.
- `client_id`: Owning or assigned synthetic client.
- `vin`: Synthetic 17-character vehicle identification number.
- `registration_plate`: Synthetic registration plate assigned to the vehicle.
- `asset_type`: Fleet asset category.
- `make`, `model`, `model_year`: Vehicle attributes.
- `fuel_type`: Petrol, diesel, hybrid, BEV, or PHEV.
- `state_registered`: Registration jurisdiction.
- `odometer_km`: Synthetic odometer reading.
- `in_service_date`: Vehicle start date.
- `lease_end_date`: Expected lease end date.
- `vehicle_status`: Operational vehicle state.
- `telematics_device_id`: Synthetic assigned telematics device identifier.
- `telematics_device_model`: Synthetic telematics hardware or OEM connection model.
- `telematics_install_date`: Synthetic installation or activation date.
- `effective_at`, `updated_at`: Required source control timestamps.

## Business-Area Tables

### `leasing_contracts.csv`
Leasing-system records for each vehicle.

- `lease_id`: Synthetic lease contract identifier.
- `vehicle_id`, `client_id`: Join keys.
- `lease_product`: Lease or management product.
- `term_months`: Contract term.
- `monthly_rental_amount`: Monthly lease rental in AUD.
- `management_fee_amount`: Monthly service-management fee in AUD.
- `included_services`: Comma-separated service bundle.
- `residual_value_amount`: Synthetic residual value estimate in AUD.
- `lease_status`: Contract status.
- `effective_at`, `updated_at`: Required source control timestamps.

### `maintenance_vendors.csv`
Synthetic supplier network for service, repairs, tyres, glass, and mobile work.

- `vendor_id`: Synthetic vendor identifier.
- `vendor_name`: Fabricated vendor name.
- `vendor_type`: Supplier category.
- `state`: Supplier state or territory.
- `preferred_vendor_flag`: Preferred network indicator.
- `average_approval_hours`: Typical approval turnaround.
- `monthly_capacity_jobs`: Synthetic capacity estimate.
- `effective_at`, `updated_at`: Required source control timestamps.

### `maintenance_work_orders.csv`
Maintenance and repair events.

- `work_order_id`: Synthetic work-order identifier.
- `vehicle_id`, `client_id`, `vendor_id`: Join keys.
- `opened_date`, `closed_date`: Work-order dates.
- `service_category`: Type of maintenance or repair.
- `odometer_km`: Odometer at service.
- `authorised_amount`: Approved amount in AUD.
- `invoice_amount`: Supplier invoice amount in AUD.
- `approval_status`: Approval outcome.
- `effective_at`, `updated_at`: Required source control timestamps.

### `fuel_cards.csv`
Vehicle-linked fuel-card accounts.

- `fuel_card_id`: Synthetic card identifier.
- `vehicle_id`, `client_id`: Join keys.
- `provider_name`: Fabricated fuel-card provider.
- `card_status`: Card lifecycle state.
- `monthly_limit_amount`: Monthly spend limit in AUD.
- `effective_at`, `updated_at`: Required source control timestamps.

### `fuel_card_transactions.csv`
Fuel-card spend and exceptions.

- `fuel_transaction_id`: Synthetic transaction identifier.
- `fuel_card_id`, `vehicle_id`, `client_id`: Join keys.
- `transaction_datetime`: Transaction timestamp.
- `merchant_state`: Merchant state or territory.
- `fuel_product`: Fuel or electricity product.
- `litres`: Litres purchased, or zero for electricity rows.
- `gross_amount`: Transaction amount in AUD.
- `exception_flag`: Potential exception indicator.

### `telematics_daily.csv`
Daily vehicle telematics summary.

- `telematics_event_id`: Synthetic telematics row identifier.
- `vehicle_id`, `client_id`: Join keys.
- `telematics_device_id`: Device producing the daily summary.
- `device_firmware_version`: Synthetic firmware version reported by the device.
- `event_date`: Summary date.
- `provider_name`: Fabricated GPS or connected-vehicle provider.
- `distance_km`: Daily distance.
- `idle_minutes`: Idle time.
- `harsh_events_count`: Harsh driving events.
- `gps_fix_rate_pct`: Daily location-data completeness.

### `insurance_claims.csv`
Accident and insurance case management.

- `claim_id`: Synthetic claim identifier.
- `claim_number`: Human-readable synthetic claim number.
- `insurer_claim_reference`: Synthetic insurer-side claim reference.
- `vehicle_id`, `client_id`: Join keys.
- `incident_date`, `claim_lodged_date`: Incident and lodgement dates.
- `incident_type`: Claim category.
- `claim_status`: Case status.
- `claim_handler_email_domain`: Synthetic domain for claim handler routing.
- `repairer_vendor_id`: Maintenance vendor assigned as repairer.
- `replacement_vehicle_required_flag`: Whether a replacement vehicle is required.
- `estimated_repair_amount`: Estimated repair cost in AUD.
- `at_fault_flag`: Fault assessment.
- `days_off_road`: Downtime estimate.
- `effective_at`, `updated_at`: Required source control timestamps.

### `vehicle_registration_events.csv`
Registration and CTP renewal management.

- `registration_event_id`: Synthetic renewal identifier.
- `vehicle_id`, `client_id`: Join keys.
- `registration_state`: Jurisdiction.
- `plate_number`: Synthetic plate number.
- `renewal_due_date`: Renewal date.
- `renewal_status`: Renewal workflow state.
- `ctp_provider`: Synthetic CTP provider or scheme.
- `renewal_amount`: Registration and CTP amount in AUD.
- `effective_at`, `updated_at`: Required source control timestamps.

### `finance_billing_invoices.csv`
Client billing and rebill lines summarized by invoice.

- `invoice_id`: Synthetic invoice identifier.
- `invoice_number`: Human-readable synthetic invoice number.
- `client_id`: Join key.
- `invoice_date`: Invoice date.
- `invoice_due_date`: Invoice payment due date.
- `billing_period`: Billing month.
- `billing_contact_email_domain`: Synthetic billing contact domain.
- `purchase_order_number`: Synthetic client purchase-order reference.
- `lease_charges_amount`: Lease charges in AUD.
- `maintenance_rebill_amount`: Maintenance rebills in AUD.
- `fuel_rebill_amount`: Fuel rebills in AUD.
- `management_fees_amount`: Service fees in AUD.
- `invoice_status`: Billing state.
- `payment_terms_days`: Payment terms in days.
- `payment_method`: Synthetic payment method.
- `effective_at`, `updated_at`: Required source control timestamps.

### `crm_client_portal_events.csv`
Client portal, CRM, and service case events.

- `portal_event_id`: Synthetic CRM event identifier.
- `portal_session_id`: Synthetic portal session identifier.
- `client_id`: Join key.
- `portal_user_id`: Synthetic portal user identifier.
- `portal_user_role`: Role of the portal user.
- `client_contact_email_domain`: Synthetic client contact domain.
- `event_datetime`: Event timestamp.
- `channel`: Client interaction channel.
- `request_reference`: Synthetic request or case reference.
- `event_type`: Client request category.
- `case_priority`: Priority classification.
- `first_response_hours`: Response-time metric.
- `sla_breach_flag`: Whether the synthetic case breached service level.
- `case_status`: Case state.
- `effective_at`, `updated_at`: Required source control timestamps.

### `driver_app_events.csv`
Driver mobile app usage.

- `driver_app_event_id`: Synthetic app event identifier.
- `vehicle_id`, `client_id`: Join keys.
- `event_datetime`: Event timestamp.
- `app_event_type`: Driver task.
- `device_platform`: App platform.
- `completion_status`: Session outcome.
- `session_duration_seconds`: Session length.

### `ev_charging_sessions.csv`
EV charging usage and reimbursement.

- `charging_session_id`: Synthetic charging session identifier.
- `vehicle_id`, `client_id`: Join keys.
- `charger_id`: Synthetic charger asset identifier.
- `charger_serial_number`: Synthetic charger serial number.
- `meter_id`: Synthetic electricity meter identifier.
- `session_start_datetime`: Session timestamp.
- `session_end_datetime`: Session end timestamp.
- `charger_location_type`: Home, depot, public, or workplace.
- `connector_type`: Charging connector type.
- `tariff_type`: Synthetic tariff category.
- `network_provider`: Fabricated charging provider.
- `energy_kwh`: Energy consumed.
- `gross_amount`: Charging cost in AUD.
- `reimbursement_status`: Reimbursement or payment state.
- `effective_at`, `updated_at`: Required source control timestamps.

### `remarketing_auction_results.csv`
End-of-lease disposal and auction outcomes.

- `remarketing_event_id`: Synthetic remarketing identifier.
- `vehicle_id`, `client_id`: Join keys.
- `auction_date`: Auction or tender date.
- `auction_channel`: Disposal channel.
- `odometer_km`: Odometer at disposal.
- `condition_grade`: Synthetic condition grade.
- `reserve_amount`: Reserve price in AUD.
- `sale_amount`: Sale price in AUD.
- `days_to_sell`: Time from listing to sale.
- `sale_status`: Disposal outcome.
- `effective_at`, `updated_at`: Required source control timestamps.
