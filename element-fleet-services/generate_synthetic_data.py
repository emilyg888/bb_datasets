import csv
import json
import random
from datetime import date, datetime, timedelta
from pathlib import Path


random.seed(42)
OUT = Path(__file__).resolve().parent

STATES = ["NSW", "VIC", "QLD", "WA", "SA", "TAS", "ACT", "NT"]
SEGMENTS = ["Government", "Utilities", "Construction", "Healthcare", "Retail", "Professional Services"]
ASSET_TYPES = ["Passenger", "SUV", "Light Commercial", "Ute", "Van", "Truck"]
FUEL_TYPES = ["Petrol", "Diesel", "Hybrid", "BEV", "PHEV"]
LEASE_PRODUCTS = ["Operating Lease", "Finance Lease", "Novated Lease", "Fleet Management Only"]
MAKE_MODELS = [
    ("Toyota", "HiLux"),
    ("Toyota", "Corolla"),
    ("Ford", "Ranger"),
    ("Hyundai", "i30"),
    ("Kia", "Sportage"),
    ("Tesla", "Model Y"),
    ("Mitsubishi", "Triton"),
    ("Isuzu", "D-MAX"),
    ("Mazda", "CX-5"),
    ("BYD", "Atto 3"),
]
STREET_NAMES = ["King", "George", "Collins", "Queen", "Pitt", "Flinders", "Adelaide", "Wellington"]
SUBURBS = ["Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide", "Hobart", "Canberra", "Darwin"]
POSTCODES = {
    "NSW": "2000",
    "VIC": "3000",
    "QLD": "4000",
    "WA": "6000",
    "SA": "5000",
    "TAS": "7000",
    "ACT": "2600",
    "NT": "0800",
}


def write_csv(name, rows, fields):
    with (OUT / name).open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def dollars(value):
    return round(value, 2)


def iso(dt):
    if isinstance(dt, datetime):
        return dt.strftime("%Y-%m-%dT%H:%M:%S")
    return dt.isoformat()


def source_dates(effective_at, offset_days):
    effective_date = datetime.fromisoformat(iso(effective_at))
    updated_date = effective_date + timedelta(days=offset_days)
    return {
        "effective_at": iso(effective_date),
        "updated_at": iso(updated_date),
    }


def synthetic_abn(index):
    return f"{50 + (index % 40):02d}{100000000 + index:09d}"


def email_domain(segment, index):
    normalized = segment.lower().replace(" ", "-")
    return f"{normalized}-client-{index:02d}.example.com"


def address(index, state):
    street = STREET_NAMES[index % len(STREET_NAMES)]
    suburb = SUBURBS[STATES.index(state)]
    return {
        "address_line_1": f"Level {(index % 18) + 1}, {100 + index} {street} Street",
        "suburb": suburb,
        "state": state,
        "postcode": POSTCODES[state],
        "country": "Australia",
    }


def synthetic_vin(index):
    return f"6SYNTH{index:011d}"


def registration_plate(index):
    return f"SYN{index:03d}{chr(65 + (index % 26))}"


clients = []
for i in range(1, 19):
    segment = random.choice(SEGMENTS)
    state = random.choice(STATES)
    start = date(2021, 1, 1) + timedelta(days=random.randint(0, 1200))
    clients.append(
        {
            "client_id": f"CLI-{i:04d}",
            "abn": synthetic_abn(i),
            "client_name": f"Synthetic {segment} Client {i:02d}",
            "industry_segment": segment,
            "email_domain": email_domain(segment, i),
            **address(i, state),
            "headquarters_state": state,
            "fleet_size_band": random.choice(["25-99", "100-249", "250-999", "1000+"]),
            "contract_start_date": iso(start),
            "client_status": random.choice(["Active", "Active", "Active", "Renewal Due", "Onboarding"]),
            **source_dates(start, 30 + i),
        }
    )

vehicles = []
for i in range(1, 151):
    client = random.choice(clients)
    make, model = random.choice(MAKE_MODELS)
    fuel = "BEV" if model in {"Model Y", "Atto 3"} else random.choice(FUEL_TYPES)
    start = date(2022, 1, 1) + timedelta(days=random.randint(0, 1150))
    term = random.choice([36, 48, 60])
    vehicles.append(
        {
            "vehicle_id": f"VEH-{i:05d}",
            "client_id": client["client_id"],
            "vin": synthetic_vin(i),
            "registration_plate": registration_plate(i),
            "asset_type": random.choice(ASSET_TYPES),
            "make": make,
            "model": model,
            "model_year": random.randint(2020, 2026),
            "fuel_type": fuel,
            "state_registered": random.choice(STATES),
            "odometer_km": random.randint(6_000, 165_000),
            "in_service_date": iso(start),
            "lease_end_date": iso(start + timedelta(days=term * 30)),
            "vehicle_status": random.choice(["In Service", "In Service", "In Service", "Pending Disposal", "Off Road"]),
            "telematics_device_id": f"TELDEV-{i:06d}",
            "telematics_device_model": random.choice(["SYN-T100", "SYN-T200", "OEM-CONNECT", "SYN-SAFETY"]),
            "telematics_install_date": iso(start + timedelta(days=random.randint(0, 14))),
            **source_dates(start, 45 + (i % 30)),
        }
    )

leases = []
for idx, vehicle in enumerate(vehicles, start=1):
    monthly_base = random.randint(520, 1850)
    service_fee = random.randint(35, 180)
    leases.append(
        {
            "lease_id": f"LES-{idx:05d}",
            "vehicle_id": vehicle["vehicle_id"],
            "client_id": vehicle["client_id"],
            "lease_product": random.choice(LEASE_PRODUCTS),
            "term_months": random.choice([36, 48, 60]),
            "monthly_rental_amount": dollars(monthly_base),
            "management_fee_amount": dollars(service_fee),
            "included_services": random.choice(
                [
                    "maintenance,fuel,registration",
                    "maintenance,accident,registration,billing",
                    "maintenance,fuel,telematics,driver_app",
                    "management_only",
                ]
            ),
            "residual_value_amount": dollars(monthly_base * random.uniform(9, 18)),
            "lease_status": random.choice(["Active", "Active", "Active", "Renewal Review", "Closed"]),
            **source_dates(datetime.fromisoformat(vehicle["in_service_date"]), 60 + (idx % 45)),
        }
    )

maintenance_vendors = []
for i in range(1, 24):
    effective = date(2020, 7, 1) + timedelta(days=i * 17)
    maintenance_vendors.append(
        {
            "vendor_id": f"MNT-VEN-{i:03d}",
            "vendor_name": f"Synthetic Service Network {i:02d}",
            "vendor_type": random.choice(["Dealer", "Tyre Network", "Independent Workshop", "Glass Repair", "Mobile Service"]),
            "state": random.choice(STATES),
            "preferred_vendor_flag": random.choice(["Y", "Y", "N"]),
            "average_approval_hours": round(random.uniform(0.4, 12.0), 1),
            "monthly_capacity_jobs": random.randint(35, 420),
            **source_dates(effective, 90 + i),
        }
    )

work_orders = []
for i in range(1, 321):
    vehicle = random.choice(vehicles)
    vendor = random.choice(maintenance_vendors)
    opened = date(2025, 1, 1) + timedelta(days=random.randint(0, 500))
    amount = random.uniform(140, 2800)
    work_orders.append(
        {
            "work_order_id": f"WO-{i:06d}",
            "vehicle_id": vehicle["vehicle_id"],
            "client_id": vehicle["client_id"],
            "vendor_id": vendor["vendor_id"],
            "opened_date": iso(opened),
            "closed_date": iso(opened + timedelta(days=random.randint(0, 10))),
            "service_category": random.choice(["Scheduled Service", "Tyres", "Brakes", "Windscreen", "Battery", "Mechanical Repair"]),
            "odometer_km": max(0, int(vehicle["odometer_km"]) + random.randint(-9000, 9000)),
            "authorised_amount": dollars(amount),
            "invoice_amount": dollars(amount * random.uniform(0.92, 1.12)),
            "approval_status": random.choice(["Approved", "Approved", "Approved", "Queried", "Declined"]),
            **source_dates(opened, random.randint(1, 12)),
        }
    )

fuel_cards = []
fuel_transactions = []
for i, vehicle in enumerate(random.sample(vehicles, 105), start=1):
    card_id = f"FUEL-{i:05d}"
    fuel_cards.append(
        {
            "fuel_card_id": card_id,
            "vehicle_id": vehicle["vehicle_id"],
            "client_id": vehicle["client_id"],
            "provider_name": random.choice(["Synthetic Fuel Network A", "Synthetic Fuel Network B", "Synthetic Multi-Fuel Card"]),
            "card_status": random.choice(["Active", "Active", "Active", "Suspended", "Cancelled"]),
            "monthly_limit_amount": dollars(random.choice([650, 900, 1200, 1800, 2500])),
            **source_dates(datetime.fromisoformat(vehicle["in_service_date"]), 20 + (i % 25)),
        }
    )
    for _ in range(random.randint(3, 8)):
        litres = 0 if vehicle["fuel_type"] == "BEV" else random.uniform(22, 84)
        fuel_transactions.append(
            {
                "fuel_transaction_id": f"FTX-{len(fuel_transactions)+1:07d}",
                "fuel_card_id": card_id,
                "vehicle_id": vehicle["vehicle_id"],
                "client_id": vehicle["client_id"],
                "transaction_datetime": iso(datetime(2025, 1, 1) + timedelta(days=random.randint(0, 500), hours=random.randint(0, 23))),
                "merchant_state": random.choice(STATES),
                "fuel_product": "Electricity" if litres == 0 else random.choice(["Unleaded", "Premium Unleaded", "Diesel"]),
                "litres": round(litres, 2),
                "gross_amount": dollars(random.uniform(18, 210) if litres else random.uniform(8, 56)),
                "exception_flag": random.choice(["N", "N", "N", "Y"]),
            }
        )

telematics = []
for vehicle in random.sample(vehicles, 85):
    base = date(2026, 3, 1)
    for d in range(14):
        telematics.append(
            {
                "telematics_event_id": f"TEL-{len(telematics)+1:07d}",
                "vehicle_id": vehicle["vehicle_id"],
                "client_id": vehicle["client_id"],
                "telematics_device_id": vehicle["telematics_device_id"],
                "device_firmware_version": random.choice(["4.2.1", "4.3.0", "5.0.2"]),
                "event_date": iso(base + timedelta(days=d)),
                "provider_name": random.choice(["Synthetic GPS Cloud", "Synthetic OEM Connect", "Synthetic Safety Telematics"]),
                "distance_km": round(random.uniform(0, 420), 1),
                "idle_minutes": random.randint(0, 95),
                "harsh_events_count": random.randint(0, 7),
                "gps_fix_rate_pct": round(random.uniform(88, 100), 2),
            }
        )

claims = []
for i in range(1, 86):
    vehicle = random.choice(vehicles)
    lodged = date(2025, 1, 1) + timedelta(days=random.randint(0, 500))
    claims.append(
        {
            "claim_id": f"CLM-{i:06d}",
            "claim_number": f"SYN-CLAIM-{2025 + (i % 2)}-{i:06d}",
            "insurer_claim_reference": f"INS-SYN-{i:07d}",
            "vehicle_id": vehicle["vehicle_id"],
            "client_id": vehicle["client_id"],
            "incident_date": iso(lodged - timedelta(days=random.randint(0, 7))),
            "claim_lodged_date": iso(lodged),
            "incident_type": random.choice(["Collision", "Windscreen", "Theft", "Weather", "Third Party Damage"]),
            "claim_status": random.choice(["Open", "Assessor Review", "Repair Authorised", "Settled", "Rejected"]),
            "claim_handler_email_domain": "claims.example.com",
            "repairer_vendor_id": random.choice(maintenance_vendors)["vendor_id"],
            "replacement_vehicle_required_flag": random.choice(["Y", "N"]),
            "estimated_repair_amount": dollars(random.uniform(450, 14500)),
            "at_fault_flag": random.choice(["Y", "N", "Unknown"]),
            "days_off_road": random.randint(0, 38),
            **source_dates(lodged, random.randint(1, 40)),
        }
    )

registrations = []
for i, vehicle in enumerate(vehicles, start=1):
    due = date(2026, 1, 1) + timedelta(days=random.randint(0, 365))
    registrations.append(
        {
            "registration_event_id": f"REG-{i:06d}",
            "vehicle_id": vehicle["vehicle_id"],
            "client_id": vehicle["client_id"],
            "registration_state": vehicle["state_registered"],
            "plate_number": vehicle["registration_plate"],
            "renewal_due_date": iso(due),
            "renewal_status": random.choice(["Current", "Current", "Due Soon", "Submitted", "Overdue"]),
            "ctp_provider": random.choice(["Synthetic CTP A", "Synthetic CTP B", "Government Scheme"]),
            "renewal_amount": dollars(random.uniform(520, 2100)),
            **source_dates(due - timedelta(days=45), random.randint(1, 45)),
        }
    )

invoices = []
for i in range(1, 241):
    client = random.choice(clients)
    invoice_date = date(2025, 1, 1) + timedelta(days=random.randint(0, 500))
    base = random.uniform(3_000, 95_000)
    invoices.append(
        {
            "invoice_id": f"INV-{i:07d}",
            "invoice_number": f"EFSA-{invoice_date.strftime('%Y%m')}-{i:06d}",
            "client_id": client["client_id"],
            "invoice_date": iso(invoice_date),
            "invoice_due_date": iso(invoice_date + timedelta(days=30)),
            "billing_period": invoice_date.strftime("%Y-%m"),
            "billing_contact_email_domain": client["email_domain"],
            "purchase_order_number": f"PO-SYN-{i:06d}",
            "lease_charges_amount": dollars(base),
            "maintenance_rebill_amount": dollars(base * random.uniform(0.02, 0.22)),
            "fuel_rebill_amount": dollars(base * random.uniform(0.01, 0.18)),
            "management_fees_amount": dollars(base * random.uniform(0.01, 0.06)),
            "invoice_status": random.choice(["Issued", "Issued", "Paid", "Part Paid", "Disputed"]),
            "payment_terms_days": 30,
            "payment_method": random.choice(["Direct Debit", "EFT", "Card", "BPAY"]),
            **source_dates(invoice_date, random.randint(1, 35)),
        }
    )

portal_events = []
for i in range(1, 421):
    client = random.choice(clients)
    event_datetime = datetime(2025, 1, 1) + timedelta(days=random.randint(0, 500), hours=random.randint(0, 23))
    portal_events.append(
        {
            "portal_event_id": f"CRM-{i:07d}",
            "portal_session_id": f"PORTAL-SESSION-{i:07d}",
            "client_id": client["client_id"],
            "portal_user_id": f"PORTAL-USER-{random.randint(1, 90):05d}",
            "portal_user_role": random.choice(["Fleet Manager", "Finance User", "Driver Coordinator", "Executive Viewer"]),
            "client_contact_email_domain": client["email_domain"],
            "event_datetime": iso(event_datetime),
            "channel": random.choice(["Client Portal", "CRM Case", "Email", "Phone"]),
            "request_reference": f"REQ-{i:07d}",
            "event_type": random.choice(["Quote Request", "Vehicle Order", "Invoice Query", "Maintenance Query", "Report Download", "Renewal Discussion"]),
            "case_priority": random.choice(["Low", "Medium", "High", "Critical"]),
            "first_response_hours": round(random.uniform(0.1, 36), 1),
            "sla_breach_flag": random.choice(["N", "N", "N", "Y"]),
            "case_status": random.choice(["Open", "Pending Client", "Resolved", "Escalated"]),
            **source_dates(event_datetime, random.randint(0, 14)),
        }
    )

driver_events = []
for i in range(1, 521):
    vehicle = random.choice(vehicles)
    driver_events.append(
        {
            "driver_app_event_id": f"APP-{i:07d}",
            "vehicle_id": vehicle["vehicle_id"],
            "client_id": vehicle["client_id"],
            "event_datetime": iso(datetime(2025, 1, 1) + timedelta(days=random.randint(0, 500), hours=random.randint(0, 23))),
            "app_event_type": random.choice(["Odometer Update", "Service Booking", "Fuel PIN Reset", "Damage Report", "Registration Reminder", "EV Charge Receipt"]),
            "device_platform": random.choice(["iOS", "Android", "Mobile Web"]),
            "completion_status": random.choice(["Completed", "Completed", "Abandoned", "Failed"]),
            "session_duration_seconds": random.randint(20, 720),
        }
    )

charging_sessions = []
ev_vehicles = [vehicle for vehicle in vehicles if vehicle["fuel_type"] in {"BEV", "PHEV"}]
for i in range(1, 361):
    vehicle = random.choice(ev_vehicles)
    kwh = random.uniform(6, 74)
    session_start = datetime(2025, 1, 1) + timedelta(days=random.randint(0, 500), hours=random.randint(0, 23))
    charging_sessions.append(
        {
            "charging_session_id": f"EVS-{i:07d}",
            "vehicle_id": vehicle["vehicle_id"],
            "client_id": vehicle["client_id"],
            "charger_id": f"CHG-{random.randint(1, 140):05d}",
            "charger_serial_number": f"CHGSYN{random.randint(100000, 999999)}",
            "meter_id": f"MTR-{random.randint(1, 220):06d}",
            "session_start_datetime": iso(session_start),
            "session_end_datetime": iso(session_start + timedelta(minutes=random.randint(28, 420))),
            "charger_location_type": random.choice(["Home", "Depot", "Public", "Workplace"]),
            "connector_type": random.choice(["Type 2", "CCS2", "CHAdeMO"]),
            "tariff_type": random.choice(["Flat", "Peak", "Off Peak", "Demand"]),
            "network_provider": random.choice(["Synthetic Charge Network A", "Synthetic Charge Network B", "Client Depot Charger"]),
            "energy_kwh": round(kwh, 2),
            "gross_amount": dollars(kwh * random.uniform(0.22, 0.78)),
            "reimbursement_status": random.choice(["Matched", "Pending", "Rejected", "Client Paid"]),
            **source_dates(session_start, random.randint(0, 21)),
        }
    )

auctions = []
for i, vehicle in enumerate(random.sample(vehicles, 65), start=1):
    reserve = random.uniform(8_000, 48_000)
    sale = reserve * random.uniform(0.82, 1.22)
    auction_date = date(2025, 1, 1) + timedelta(days=random.randint(0, 500))
    auctions.append(
        {
            "remarketing_event_id": f"RMK-{i:06d}",
            "vehicle_id": vehicle["vehicle_id"],
            "client_id": vehicle["client_id"],
            "auction_date": iso(auction_date),
            "auction_channel": random.choice(["Wholesale Auction", "Online Auction", "Tender", "Dealer Direct"]),
            "odometer_km": vehicle["odometer_km"],
            "condition_grade": random.choice(["A", "B", "C", "D"]),
            "reserve_amount": dollars(reserve),
            "sale_amount": dollars(sale),
            "days_to_sell": random.randint(3, 54),
            "sale_status": random.choice(["Sold", "Sold", "Sold", "Passed In", "Pending Settlement"]),
            **source_dates(auction_date, random.randint(3, 60)),
        }
    )

tables = {
    "clients.csv": clients,
    "vehicles.csv": vehicles,
    "leasing_contracts.csv": leases,
    "maintenance_vendors.csv": maintenance_vendors,
    "maintenance_work_orders.csv": work_orders,
    "fuel_cards.csv": fuel_cards,
    "fuel_card_transactions.csv": fuel_transactions,
    "telematics_daily.csv": telematics,
    "insurance_claims.csv": claims,
    "vehicle_registration_events.csv": registrations,
    "finance_billing_invoices.csv": invoices,
    "crm_client_portal_events.csv": portal_events,
    "driver_app_events.csv": driver_events,
    "ev_charging_sessions.csv": charging_sessions,
    "remarketing_auction_results.csv": auctions,
}

for name, rows in tables.items():
    write_csv(name, rows, list(rows[0].keys()))

metadata = {
    "name": "element_fleet_services_synthetic",
    "domain": "fleet_management",
    "description": "Synthetic Australian fleet-management datasets inspired by public information about Custom Fleet Australia / Element Fleet Services Australia Pty Ltd business areas.",
    "entity": "ELEMENT FLEET SERVICES AUSTRALIA PTY LTD / Custom Fleet Australia",
    "synthetic": True,
    "privacy": "No real customers, drivers, vehicles, vendors, invoices, claims, GPS traces, or transactions are represented.",
    "created_by": "Codex",
    "version": "1.0",
    "tables": {name: {"row_count": len(rows), "columns": list(rows[0].keys())} for name, rows in tables.items()},
}

(OUT / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
