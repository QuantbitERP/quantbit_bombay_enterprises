# Copyright (c) 2026, Quantbit Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, formatdate, getdate, money_in_words, today


def execute(filters=None):
    filters = frappe._dict(filters or {})
    validate_filters(filters)
    return get_columns(), get_data(filters)


def validate_filters(filters):
    if not filters.get("from_date") or not filters.get("to_date"):
        frappe.throw(_("From Date and To Date are mandatory"))
    if getdate(filters.from_date) > getdate(filters.to_date):
        frappe.throw(_("From Date cannot be after To Date"))
    if not filters.get("company"):
        frappe.throw(_("Company is mandatory"))


def get_columns():
    return [
        {"label": _("Sr No."), "fieldname": "sr_no", "fieldtype": "Int", "width": 70},
        {"label": _("Received From"), "fieldname": "party_name", "fieldtype": "Data", "width": 240},
        {"label": _("Cheque No"), "fieldname": "reference_no", "fieldtype": "Data", "width": 120},
        {"label": _("Cheque Date"), "fieldname": "reference_date", "fieldtype": "Date", "width": 110},
        {"label": _("Bank Name"), "fieldname": "bank_name", "fieldtype": "Data", "width": 200},
        {"label": _("Bank Branch"), "fieldname": "bank_branch", "fieldtype": "Data", "width": 160},
        {"label": _("Amount"), "fieldname": "paid_amount", "fieldtype": "Currency", "width": 130},
        # {
        #   "label": _("Payment Entry"),
        #   "fieldname": "payment_entry",
        #   "fieldtype": "Link",
        #   "options": "Payment Entry",
        #   "width": 160,
        # },
    ]


def get_data(filters):
    conditions = ""
    if filters.get("bank_account"):
        # Payment Entry.bank_account = "Company Bank Account"
        conditions += " AND pe.bank_account = %(bank_account)s"

    rows = frappe.db.sql(
        f"""
        SELECT
            pe.name AS payment_entry,
            pe.party_name,
            pe.reference_no,
            pe.reference_date,
            ba.bank AS bank_name,
            ba.custom_branch_name AS bank_branch,
            pe.paid_amount
        FROM `tabPayment Entry` pe
        LEFT JOIN `tabBank Account` ba ON ba.name = pe.party_bank_account
        WHERE pe.docstatus = 1
            AND pe.payment_type = 'Receive'
            AND pe.mode_of_payment = 'Cheque'
            AND pe.company = %(company)s
            AND pe.posting_date BETWEEN %(from_date)s AND %(to_date)s
            {conditions}
        ORDER BY pe.posting_date, pe.creation
        """,
        filters,
        as_dict=True,
    )

    total = sum(flt(r.paid_amount) for r in rows)
    header = get_slip_header(filters, total)

    for idx, row in enumerate(rows, 1):
        row.sr_no = idx
        # extra keys are not shown in the report grid, they are only used by the print format
        row.update(header)

    return rows


def get_slip_header(filters, total):
    """Details of the company bank account (is_company_account = 1) + company info for the slip."""
    bank_account = filters.get("bank_account")
    if not bank_account:
        found = frappe.get_all(
            "Bank Account",
            filters={"is_company_account": 1, "disabled": 0, "company": filters.company},
            fields=["name"],
            order_by="is_default desc, creation asc",
            limit=1,
        )
        bank_account = found[0].name if found else None

    ba = frappe._dict()
    if bank_account:
        ba = frappe.db.get_value(
            "Bank Account",
            bank_account,
            ["bank", "custom_branch_name", "bank_account_no", "custom_bank_holder_name", "account_name"],
            as_dict=True,
        ) or frappe._dict()

    company = frappe.db.get_value(
        "Company", filters.company, ["pan", "phone_no", "default_currency"], as_dict=True
    ) or frappe._dict()

    return {
        "co_bank_name": ba.get("bank") or "",
        "co_branch_name": ba.get("custom_branch_name") or "",
        "co_account_no": ba.get("bank_account_no") or "",
        "co_account_holder": ba.get("custom_bank_holder_name") or ba.get("account_name") or "",
        "co_pan": company.get("pan") or "",
        "co_phone": company.get("phone_no") or "",
        "slip_date": formatdate(today()),
        "slip_total": total,
        "amount_in_words": money_in_words(total, company.get("default_currency")),
    }