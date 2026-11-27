import frappe
from frappe import _
from frappe.desk.query_report import run
from frappe.model.mapper import get_mapped_doc
from frappe.utils import flt


def get_dashboard_data(data=None):
    if not data:
        data = frappe._dict()

    transactions = data.get("transactions", [])
    found = any("Material Inward" in group.get("items", []) for group in transactions)

    if not found:
        for group in transactions:
            if group.get("label") in ["Reference", _("Reference"), "Transactions", _("Transactions")]:
                group.setdefault("items", []).append("Material Inward")
                found = True
                break
        if not found:
            transactions.append({
                "label": _("Reference"),
                "items": ["Material Inward"],
            })

    data["transactions"] = transactions
    return data


@frappe.whitelist()
def make_material_inward(source_name, target_doc=None):
    """Map a Sales Order and its items into a new Material Inward document."""
    def set_missing_values(source, target):
        target.party_type = "Customer"
        target.customer = source.customer
        target.customer_name = source.customer_name
        target.company = source.company
        target.posting_date = frappe.utils.today()
        target.sales_order = source.name
        target.sale_order_date = source.transaction_date
        target.issue = source.custom_issue
        if not target.remarks:
            target.remarks = source.get("custom_remark") or _("Created from Sales Order {0}").format(source.name)

        total_qty = 0.0
        for item in target.items:
            if item.item and not item.part_number:
                item.part_number = frappe.db.get_value("Item", item.item, "custom_part_number")
            total_qty += flt(item.quantity)
        target.total_quantity = total_qty

    return get_mapped_doc(
        "Sales Order",
        source_name,
        {
            "Sales Order": {
                "doctype": "Material Inward",
                "field_map": {
                    "company": "company",
                    "customer": "customer",
                    "customer_name": "customer_name",
                    "name": "sales_order",
                    "transaction_date": "sale_order_date",
                },
            },
            "Sales Order Item": {
                "doctype": "Material Inward Item",
                "field_map": {
                    "item_code": "item",
                    "item_name": "item_name",
                    "description": "description",
                    "uom": "uom",
                    "qty": "quantity",
                },
            },
        },
        target_doc,
        set_missing_values,
    )


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
