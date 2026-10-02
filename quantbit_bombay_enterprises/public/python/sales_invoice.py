# Copyright (c) 2026, Quantbit Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.mapper import get_mapped_doc
from frappe.utils import flt


def get_dashboard_data(data=None):
	if not data:
		data = frappe._dict()

	transactions = data.get("transactions", [])
	found = any("Material Outward" in group.get("items", []) for group in transactions)

	if not found:
		for group in transactions:
			if group.get("label") in ["Reference", _("Reference"), "Transactions", _("Transactions")]:
				group.setdefault("items", []).append("Material Outward")
				found = True
				break
		if not found:
			transactions.append({
				"label": _("Reference"),
				"items": ["Material Outward"]
			})

	data["transactions"] = transactions

	if not data.get("non_standard_fieldnames"):
		data["non_standard_fieldnames"] = {}

	data["non_standard_fieldnames"]["Material Outward"] = "sales_invoice"

	return data


@frappe.whitelist()
def make_material_outward(source_name, target_doc=None):
	def set_missing_values(source, target):
		target.party_type = "Customer"
		target.customer = source.customer
		target.customer_name = source.customer_name
		target.company = source.company
		target.posting_date = frappe.utils.today()
		target.sales_invoice = source.name
		target.remarks = _("Created from Sales Invoice {0}").format(source.name)

		total_qty = 0.0
		for item in target.items:
			total_qty += flt(item.quantity)
		target.total_quantity = total_qty

	doclist = get_mapped_doc(
		"Sales Invoice",
		source_name,
		{
			"Sales Invoice": {
				"doctype": "Material Outward",
				"field_map": {
					"customer": "customer",
					"customer_name": "customer_name",
					"company": "company",
					"name": "sales_invoice",
				},
			},
			"Sales Invoice Item": {
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
	return doclist
