
import frappe
from frappe.utils import flt, getdate


@frappe.whitelist()
def get_warehouse_stock_on_date(item_code, posting_date=None, company=None):
    if not item_code:
        return []

    if not posting_date:
        posting_date = frappe.utils.today()

    target_date = getdate(posting_date)

    if not company:
        company = (
            frappe.defaults.get_user_default("Company")
            or frappe.db.get_single_value("Global Defaults", "default_company")
        )

    if not company:
        frappe.throw("Please select a Company.")

    # Stock movement on the selected date only.
    # Positive actual_qty means stock inward.
    stock_data = frappe.db.sql(
        """
        SELECT
            sle.warehouse,
            SUM(sle.actual_qty) AS stock_added
        FROM `tabStock Ledger Entry` sle
        INNER JOIN `tabWarehouse` w
            ON w.name = sle.warehouse
        WHERE
            sle.company = %(company)s
            AND sle.item_code = %(item_code)s
            AND sle.posting_date = %(target_date)s
            AND sle.actual_qty > 0
            AND sle.is_cancelled = 0
            AND w.company = %(company)s
        GROUP BY sle.warehouse
        HAVING SUM(sle.actual_qty) > 0
        ORDER BY sle.warehouse
        """,
        {
            "company": company,
            "item_code": item_code,
            "target_date": target_date,
        },
        as_dict=True,
    )

    # Current projected quantity from Bin
    bins = frappe.get_all(
        "Bin",
        filters={"item_code": item_code},
        fields=["warehouse", "projected_qty"],
    )

    projected_map = {
        row.warehouse: flt(row.projected_qty)
        for row in bins
    }

    results = []

    for row in stock_data:
        results.append({
            "warehouse": row.warehouse,
            "stock_added": flt(row.stock_added),
            "projected_qty": projected_map.get(row.warehouse, 0.0),
        })

    return results