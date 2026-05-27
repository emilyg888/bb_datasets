# Business Model Summary

This summary synthesizes public information about Custom Fleet Australia and Element Fleet Management into a practical fleet-management business model for dataset design. It is not based on internal company data.

## Company Context

Custom Fleet Australia operates as a fleet leasing and fleet-management provider across Australia and New Zealand and is part of Element Fleet Management. Public materials describe Custom Fleet as supporting business, government, and institutional fleets through vehicle leasing, fleet management, driver support, supplier coordination, compliance administration, and analytics.

Element Fleet describes its broader model as end-to-end fleet lifecycle management, spanning vehicle acquisition, financing, maintenance, route optimization, risk management, electric vehicle integration, and remarketing. Its public financial commentary emphasizes both net financing revenue and service revenue, with services acting as a capital-light growth component.

## Core Value Proposition

The business helps clients reduce the administrative, financial, operational, and compliance burden of running vehicle fleets. Instead of clients separately managing financing, maintenance providers, fuel cards, insurance incidents, registration renewals, driver support, telematics, billing, and end-of-lease disposal, Custom Fleet coordinates these activities through managed services, supplier networks, digital tools, and consolidated reporting.

The client benefit is framed around:

- Lower fleet administration effort.
- Better cost visibility and consolidated billing.
- Improved vehicle uptime and driver continuity.
- Access to supplier networks and negotiated service pathways.
- Safer and more compliant fleet operations.
- Data-led decisions about replacement, utilization, fuel, emissions, and EV transition.

## Customer Segments

Likely customer groups include:

- Corporate fleets with passenger, light commercial, and utility vehicles.
- Government and public-sector fleets.
- Utilities, construction, healthcare, retail, and field-service organizations.
- Employers offering novated lease or salary-packaging style vehicle programs.
- Organizations planning fleet decarbonization or EV transition.

The synthetic dataset uses broad segment labels rather than real customer names.

## Revenue Logic

The public model points to a blended finance-and-services revenue structure:

- Lease and financing income from operating leases, finance leases, novated leases, and sale/leaseback-style fleet funding.
- Recurring management fees for fleet administration and bundled services.
- Maintenance and accident-management fees or rebill administration.
- Fuel-card and transaction-linked service economics.
- Registration, CTP, tolls, infringements, and compliance administration fees.
- Telematics, reporting, analytics, and digital platform fees.
- Insurance, risk, accident, repair, and recovery-related service revenue.
- Remarketing proceeds, fees, or gains from end-of-lease disposal activity.
- EV advisory, charging infrastructure coordination, charging data, and reimbursement administration.

The dataset reflects this by separating lease charges, management fees, maintenance rebills, fuel rebills, claims, telematics, charging, and auction outcomes.

## Operating Model

The operating model is built around the vehicle lifecycle.

### 1. Acquire and Lease

Vehicles are sourced, financed, assigned to clients, and placed under a lease or fleet-management product. Lease records track contract type, term, monthly rental, service bundle, residual estimate, and lease status.

Synthetic tables:

- `clients.csv`
- `vehicles.csv`
- `leasing_contracts.csv`

### 2. Manage Daily Operations

Once vehicles are in service, the fleet manager coordinates routine operations: maintenance, tyres, fuel cards, driver support, registration, CTP, and compliance reminders. This reduces client administration and creates operational data that can be used for billing, reporting, exception management, and cost control.

Synthetic tables:

- `maintenance_vendors.csv`
- `maintenance_work_orders.csv`
- `fuel_cards.csv`
- `fuel_card_transactions.csv`
- `vehicle_registration_events.csv`
- `driver_app_events.csv`

### 3. Support Incidents and Risk

Public Custom Fleet accident-management materials describe driver support, claim lodgement, repair allocation, replacement vehicles, recovery, repairer networks, and portal visibility. This maps to a claims-management workflow with incident dates, claim statuses, estimated repair costs, fault assessment, and downtime.

Synthetic table:

- `insurance_claims.csv`

### 4. Add Data, Portals, and Analytics

Fleet portals, CRM workflows, telematics, and reporting provide visibility into utilization, safety, driver behavior, cases, invoices, and service status. These systems support both client service and advisory offerings.

Synthetic tables:

- `crm_client_portal_events.csv`
- `telematics_daily.csv`
- `finance_billing_invoices.csv`

### 5. Electrify and Optimize

Custom Fleet public EV materials describe fleet analysis, charging infrastructure advice, driver change management, whole-of-life cost review, and integrated reporting. EV charging data introduces new operational flows such as charging networks, home/depot/public charging, energy consumption, reimbursement, and charging cost allocation.

Synthetic table:

- `ev_charging_sessions.csv`

### 6. Dispose and Remarketing

At end of lease, vehicles are returned, assessed, and sold through remarketing or auction channels. Disposal outcomes affect residual risk, client replacement planning, and total cost of ownership.

Synthetic table:

- `remarketing_auction_results.csv`

## Data Design Implications

The model is naturally centered on three shared entities:

- Client: the commercial relationship and billing account.
- Vehicle: the operational asset moving through the lifecycle.
- Supplier or provider: the external network used for maintenance, fuel, charging, repair, insurance, registration, and auction activity.

This is why most tables include `client_id` and many include `vehicle_id`. The structure supports analytics such as:

- Cost per vehicle by lease product.
- Maintenance spend and approval performance by vendor.
- Fuel and EV charging cost comparison.
- Accident frequency, repair cost, and days off road.
- Registration renewal risk by state.
- Portal case volumes and response times.
- Driver app completion rates.
- Telematics utilization and safety events.
- Auction performance against reserve value.

Mutable source tables should carry source control timestamps. In this dataset, `effective_at` and `updated_at` are required on master and workflow records whose business state can change, including clients, vehicles, leases, vendors, work orders, fuel cards, claims, registration renewals, invoices, CRM cases, EV charging reimbursements, and remarketing outcomes. Pure event logs such as fuel-card transactions, telematics daily readings, and driver app activity are treated as immutable observations.

## Research Sources

- Custom Fleet Australia home page: https://www.customfleet.com.au/
- Custom Fleet lease options: https://www.customfleet.com.au/lease/lease-options
- Custom Fleet accident management: https://www.customfleet.com.au/manage/accident-management
- Custom Fleet registration and CTP: https://www.customfleet.com.au/manage/registration-and-ctp
- Custom Fleet driver guide: https://www.customfleet.com.au/driver-support/index.html
- Custom Fleet EV program: https://www.customfleet.com.au/electric-vehicles/
- Element Fleet Management home page: https://www.elementfleet.com/
- Element 2025 financial results release: https://www.elementfleet.com/about/news/element-reports-fourth-quarter-and-record-2025-financial-results-raises-common-dividend-and-provides-full-year-2026-guidance
- Element 2024 Annual Information Form mirror: https://financialreports.eu/filings/element-fleet-management-corp/annual-report/2025/13771491/

Research date: 2026-05-26.
