import frappe
from frappe.desk.query_report import run
from frappe.utils import flt


@frappe.whitelist()
def get_warehouse_stock_on_date(item_code, posting_date, company):
    if not item_code or not posting_date or not company:
        return []

    filters = {
        "company": company,
        "item_code": [item_code],
        "from_date": posting_date,
        "to_date": posting_date,
    }

    report_result = run(
        "Stock Balance",
        filters=filters,
        ignore_prepared_report=True,
    )

    result = report_result.get("result") or []
    warehouses = []

    for row in result:
        if not isinstance(row, dict):
            continue

        if row.get("item_code") != item_code:
            continue

        warehouse = row.get("warehouse")
        if not warehouse:
            continue

        available_qty = flt(
            row.get("bal_qty", row.get("balance_qty", 0))
        )

        if available_qty > 0:
            warehouses.append({
                "warehouse": warehouse,
                "available_qty": available_qty,
            })

    return warehouses
