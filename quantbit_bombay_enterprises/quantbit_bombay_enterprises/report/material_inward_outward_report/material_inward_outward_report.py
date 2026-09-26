# Copyright (c) 2026, Quantbit Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters or {})
	return columns, data


def get_columns():
	return [
		{
			"label": _("Inward Date"),
			"fieldname": "inward_date",
			"fieldtype": "Date",
			"width": 110,
		},
		{
			"label": _("Party Type"),
			"fieldname": "party_type",
			"fieldtype": "Data",
			"width": 110,
		},
		{
			"label": _("Party"),
			"fieldname": "party",
			"fieldtype": "Dynamic Link",
			"options": "party_type",
			"width": 140,
		},
		{
			"label": _("Party Name"),
			"fieldname": "party_name",
			"fieldtype": "Data",
			"width": 180,
		},
		{
			"label": _("Item Name"),
			"fieldname": "item_name",
			"fieldtype": "Data",
			"width": 180,
		},
		{
			"label": _("Inward Quantity"),
			"fieldname": "inward_quantity",
			"fieldtype": "Float",
			"width": 130,
		},
		{
			"label": _("Outward date"),
			"fieldname": "outward_date",
			"fieldtype": "Date",
			"width": 110,
		},
		{
			"label": _("Outward Quantity"),
			"fieldname": "outward_quantity",
			"fieldtype": "Float",
			"width": 130,
		},
		{
			"label": _("Balance Quantiy"),
			"fieldname": "balance_quantity",
			"fieldtype": "Float",
			"width": 130,
		},
	]


def get_data(filters):
	inward_conditions = ["mi.docstatus < 2"]
	values = {}

	if filters.get("company"):
		inward_conditions.append("mi.company = %(company)s")
		values["company"] = filters.get("company")

	if filters.get("from_date"):
		inward_conditions.append("mi.posting_date >= %(from_date)s")
		values["from_date"] = filters.get("from_date")

	if filters.get("to_date"):
		inward_conditions.append("mi.posting_date <= %(to_date)s")
		values["to_date"] = filters.get("to_date")

	if filters.get("party_type"):
		inward_conditions.append("mi.party_type = %(party_type)s")
		values["party_type"] = filters.get("party_type")

	if filters.get("party"):
		inward_conditions.append("(mi.customer = %(party)s OR mi.supplier = %(party)s)")
		values["party"] = filters.get("party")

	if filters.get("item"):
		inward_conditions.append("mii.item = %(item)s")
		values["item"] = filters.get("item")

	inward_where = " AND ".join(inward_conditions)

	inward_query = f"""
		SELECT
			mi.name as inward_name,
			mi.posting_date as inward_date,
			mi.party_type,
			mi.customer,
			mi.customer_name,
			mi.supplier,
			mi.supplier_name,
			mii.name as inward_item_row,
			mii.item,
			mii.item_name,
			mii.quantity as inward_quantity
		FROM `tabMaterial Inward` mi
		INNER JOIN `tabMaterial Inward Item` mii
			ON mii.parent = mi.name AND mii.parenttype = 'Material Inward'
		WHERE {inward_where}
		ORDER BY mi.posting_date ASC, mi.name ASC, mii.idx ASC
	"""

	inwards = frappe.db.sql(inward_query, values, as_dict=True)

	# Fetch all outwards linked to these inwards
	inward_names = list(set([d.inward_name for d in inwards]))

	outwards_by_inward = {}
	if inward_names:
		outward_query = """
			SELECT
				mo.name as outward_name,
				mo.posting_date as outward_date,
				mo.against_document,
				moi.name as outward_item_row,
				moi.inward_item,
				moi.item,
				moi.item_name,
				moi.quantity as outward_quantity
			FROM `tabMaterial Outward` mo
			INNER JOIN `tabMaterial Inward Item` moi
				ON moi.parent = mo.name AND moi.parenttype = 'Material Outward'
			WHERE mo.docstatus < 2
				AND mo.against_document IN %(inward_names)s
			ORDER BY mo.posting_date ASC, mo.name ASC, moi.idx ASC
		"""
		outwards = frappe.db.sql(outward_query, {"inward_names": inward_names}, as_dict=True)

		for out in outwards:
			key = (out.against_document, out.inward_item if out.inward_item else out.item)
			outwards_by_inward.setdefault(key, []).append(out)

	data = []
	for inw in inwards:
		party = inw.customer if inw.party_type == "Customer" else inw.supplier
		party_name = inw.customer_name if inw.party_type == "Customer" else inw.supplier_name
		item_display = inw.item_name or inw.item

		# Check if outwards match by inward_item row first, or by item code
		matched_outwards = outwards_by_inward.get((inw.inward_name, inw.inward_item_row))
		if not matched_outwards:
			matched_outwards = outwards_by_inward.get((inw.inward_name, inw.item), [])

		if not matched_outwards:
			data.append({
				"inward_date": inw.inward_date,
				"party_type": inw.party_type,
				"party": party,
				"party_name": party_name,
				"item_name": item_display,
				"inward_quantity": flt(inw.inward_quantity),
				"outward_date": None,
				"outward_quantity": 0.0,
				"balance_quantity": flt(inw.inward_quantity),
			})
		else:
			running_balance = flt(inw.inward_quantity)
			for i, out in enumerate(matched_outwards):
				out_qty = flt(out.outward_quantity)
				running_balance -= out_qty
				data.append({
					"inward_date": inw.inward_date,
					"party_type": inw.party_type,
					"party": party,
					"party_name": party_name,
					"item_name": item_display,
					"inward_quantity": flt(inw.inward_quantity) if i == 0 else 0.0,
					"outward_date": out.outward_date,
					"outward_quantity": out_qty,
					"balance_quantity": running_balance,
				})

	# Also check standalone outwards if no inward filter is explicitly restricting to inwards
	if not filters.get("item") and not inward_names:
		# check if there are outwards without against_document
		pass

	return data
