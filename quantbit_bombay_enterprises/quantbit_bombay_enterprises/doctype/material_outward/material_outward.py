# Copyright (c) 2026, Quantbit Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class MaterialOutward(Document):
	def validate(self):
		self.validate_party()
		self.validate_against_document()
		self.validate_items()

	def validate_party(self):
		if not self.party_type:
			self.party_type = "Customer"

		if self.party_type == "Customer":
			if not self.customer:
				frappe.throw(_("Customer is mandatory when Party Type is Customer"))
			if not self.customer_name:
				self.customer_name = frappe.db.get_value("Customer", self.customer, "customer_name")
			self.supplier = None
			self.supplier_name = None
		elif self.party_type == "Supplier":
			if not self.supplier:
				frappe.throw(_("Supplier is mandatory when Party Type is Supplier"))
			if not self.supplier_name:
				self.supplier_name = frappe.db.get_value("Supplier", self.supplier, "supplier_name")
			self.customer = None
			self.customer_name = None

	def validate_against_document(self):
		if self.against_document:
			inward = frappe.get_doc("Material Inward", self.against_document)
			if inward.party_type != self.party_type:
				frappe.throw(
					_("Against Document {0} is of Party Type '{1}', but selected Party Type is '{2}'").format(
						self.against_document, inward.party_type, self.party_type
					)
				)
			if self.party_type == "Customer" and inward.customer != self.customer:
				frappe.throw(
					_("Against Document {0} belongs to Customer '{1}', not '{2}'").format(
						self.against_document, inward.customer, self.customer
					)
				)
			if self.party_type == "Supplier" and inward.supplier != self.supplier:
				frappe.throw(
					_("Against Document {0} belongs to Supplier '{1}', not '{2}'").format(
						self.against_document, inward.supplier, self.supplier
					)
				)

			if not self.party_receipt_no and inward.party_receipt_no:
				self.party_receipt_no = inward.party_receipt_no

	def validate_items(self):
		if not self.items:
			frappe.throw(_("Please add at least one item in the Items table"))

		total_qty = 0.0
		for row in self.items:
			if not row.item:
				frappe.throw(_("Row #{0}: Item is required").format(row.idx))
			if flt(row.quantity) <= 0:
				frappe.throw(_("Row #{0}: Quantity must be greater than 0 for Item {1}").format(row.idx, row.item))

			if not row.item_name or not row.uom:
				item_doc = frappe.db.get_value(
					"Item",
					row.item,
					["item_name", "stock_uom", "description"],
					as_dict=True
				)
				if item_doc:
					if not row.item_name:
						row.item_name = item_doc.item_name
					if not row.uom:
						row.uom = item_doc.stock_uom
					if not row.description:
						row.description = item_doc.description

			total_qty += flt(row.quantity)

		self.total_quantity = total_qty


@frappe.whitelist()
def get_inward_details(inward_name):
	if not inward_name or not frappe.db.exists("Material Inward", inward_name):
		return None

	doc = frappe.get_doc("Material Inward", inward_name)
	items = []
	for item in doc.items:
		items.append({
			"item": item.item,
			"item_name": item.item_name,
			"description": item.description,
			"uom": item.uom,
			"quantity": item.quantity,
			"inward_item": item.name
		})

	return {
		"company": doc.company,
		"party_type": doc.party_type,
		"customer": doc.customer,
		"customer_name": doc.customer_name,
		"supplier": doc.supplier,
		"supplier_name": doc.supplier_name,
		"party_receipt_no": doc.party_receipt_no,
		"items": items
	}
