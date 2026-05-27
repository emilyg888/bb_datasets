import csv
from datetime import datetime, timedelta
from pathlib import Path


BASE = Path(__file__).resolve().parent
DELTA_BASE = BASE / "delta_sources"
DELTA_DATES = ["2026-05-25", "2026-05-26", "2026-05-27", "2026-05-28"]

TABLE_DELTAS = {
    "clients.csv": ["client_status", "fleet_size_band"],
    "vehicles.csv": ["odometer_km", "vehicle_status"],
    "leasing_contracts.csv": ["lease_status", "management_fee_amount"],
    "maintenance_vendors.csv": ["preferred_vendor_flag", "monthly_capacity_jobs"],
    "maintenance_work_orders.csv": ["approval_status", "invoice_amount"],
    "fuel_cards.csv": ["card_status", "monthly_limit_amount"],
    "insurance_claims.csv": ["claim_status", "days_off_road"],
    "vehicle_registration_events.csv": ["renewal_status", "renewal_amount"],
    "finance_billing_invoices.csv": ["invoice_status"],
    "crm_client_portal_events.csv": ["case_status", "case_priority"],
    "ev_charging_sessions.csv": ["reimbursement_status"],
    "remarketing_auction_results.csv": ["sale_status", "sale_amount"],
}

STATUS_VALUES = {
    "client_status": ["Active", "Renewal Due", "Onboarding"],
    "vehicle_status": ["In Service", "Pending Disposal", "Off Road"],
    "lease_status": ["Active", "Renewal Review", "Closed"],
    "preferred_vendor_flag": ["Y", "N"],
    "approval_status": ["Approved", "Queried", "Declined"],
    "card_status": ["Active", "Suspended", "Cancelled"],
    "claim_status": ["Open", "Assessor Review", "Repair Authorised", "Settled"],
    "renewal_status": ["Current", "Due Soon", "Submitted", "Overdue"],
    "invoice_status": ["Issued", "Paid", "Part Paid", "Disputed"],
    "case_status": ["Open", "Pending Client", "Resolved", "Escalated"],
    "case_priority": ["Low", "Medium", "High", "Critical"],
    "reimbursement_status": ["Matched", "Pending", "Rejected", "Client Paid"],
    "sale_status": ["Sold", "Passed In", "Pending Settlement"],
}


def read_rows(path):
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def write_rows(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def mutate_value(column, value, date_index, row_index):
    if column in STATUS_VALUES:
        values = STATUS_VALUES[column]
        return values[(values.index(value) + 1) % len(values)] if value in values else values[0]
    if column == "fleet_size_band":
        values = ["25-99", "100-249", "250-999", "1000+"]
        return values[(values.index(value) + 1) % len(values)] if value in values else "100-249"
    if column == "odometer_km":
        return str(int(float(value)) + 120 + date_index * 85 + row_index)
    if column == "monthly_capacity_jobs":
        return str(int(float(value)) + 5 + date_index)
    if column == "days_off_road":
        return str(int(float(value)) + 1 + date_index)
    if column in {"management_fee_amount", "invoice_amount", "renewal_amount", "monthly_limit_amount", "sale_amount"}:
        return f"{float(value) * (1.01 + date_index * 0.005):.2f}"
    return value


def delta_rows(table_name, rows, delta_date, date_index):
    extract_dt = datetime.fromisoformat(delta_date)
    sample_size = min(8, len(rows))
    start = date_index * sample_size
    selected = [rows[(start + offset) % len(rows)] for offset in range(sample_size)]
    output = []
    for row_index, row in enumerate(selected, start=1):
        changed = dict(row)
        for column in TABLE_DELTAS[table_name]:
            changed[column] = mutate_value(column, changed[column], date_index, row_index)
        changed["effective_at"] = (extract_dt - timedelta(hours=9, minutes=row_index)).strftime("%Y-%m-%dT%H:%M:%S")
        changed["updated_at"] = (extract_dt + timedelta(hours=8, minutes=row_index)).strftime("%Y-%m-%dT%H:%M:%S")
        changed["delta_action"] = "UPDATE"
        output.append(changed)
    return output


def main():
    for date_index, delta_date in enumerate(DELTA_DATES):
        manifest = []
        for table_name in TABLE_DELTAS:
            rows = read_rows(BASE / table_name)
            deltas = delta_rows(table_name, rows, delta_date, date_index)
            fields = list(rows[0].keys()) + ["delta_action"]
            write_rows(DELTA_BASE / delta_date / table_name, deltas, fields)
            manifest.append(
                {
                    "source_date": delta_date,
                    "table_name": table_name,
                    "row_count": len(deltas),
                    "delta_type": "synthetic_update_extract",
                }
            )
        write_rows(
            DELTA_BASE / delta_date / "manifest.csv",
            manifest,
            ["source_date", "table_name", "row_count", "delta_type"],
        )


if __name__ == "__main__":
    main()
