# Copyright (c) 2026, Quantbit Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.mapper import get_mapped_doc


def get_dashboard_data(data=None):
	if not data:
		data = frappe._dict()

	transactions = data.get("transactions", [])

	quotation_found = any("Quotation" in group.get("items", []) for group in transactions)
	material_inward_found = any("Material Inward" in group.get("items", []) for group in transactions)

	if not quotation_found or not material_inward_found:
		tx_group = None
		for group in transactions:
			if group.get("label") in ["Transactions", _("Transactions")]:
				tx_group = group
				break
		if not tx_group:
			tx_group = {"label": _("Transactions"), "items": []}
			transactions.append(tx_group)

		if not quotation_found:
			tx_group["items"].append("Quotation")
		if not material_inward_found:
			tx_group["items"].append("Material Inward")

	data["transactions"] = transactions

	if not data.get("non_standard_fieldnames"):
		data["non_standard_fieldnames"] = {}

	data["non_standard_fieldnames"]["Quotation"] = "custom_issue"
	data["non_standard_fieldnames"]["Material Inward"] = "issue"

	return data


@frappe.whitelist()
def make_quotation(source_name, target_doc=None):
	def set_missing_values(source, target):
		target.quotation_to = "Customer"
		if source.customer:
			target.party_name = source.customer
			target.customer_name = source.customer_name
		target.custom_issue = source.name
		if source.company:
			target.company = source.company

	doclist = get_mapped_doc(
		"Issue",
		source_name,
		{
			"Issue": {
				"doctype": "Quotation",
				"field_map": {
					"name": "custom_issue",
					"customer": "party_name",
					"customer_name": "customer_name",
					"company": "company",
				},
			}
		},
		target_doc,
		set_missing_values,
	)
	return doclist


@frappe.whitelist()
def make_material_inward(source_name, target_doc=None):
	def set_missing_values(source, target):
		target.party_type = "Customer"
		if source.customer:
			target.customer = source.customer
			target.customer_name = source.customer_name
		target.issue = source.name
		if source.company:
			target.company = source.company

	doclist = get_mapped_doc(
		"Issue",
		source_name,
		{
			"Issue": {
				"doctype": "Material Inward",
				"field_map": {
					"name": "issue",
					"customer": "customer",
					"customer_name": "customer_name",
					"company": "company",
				},
			}
		},
		target_doc,
		set_missing_values,
	)
	return doclist
