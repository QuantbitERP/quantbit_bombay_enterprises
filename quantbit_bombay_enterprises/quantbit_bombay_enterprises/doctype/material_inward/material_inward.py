# Copyright (c) 2026, Quantbit Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class MaterialInward(Document):
	def validate(self):
		self.validate_party()
		self.validate_sales_order()
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
			self.sales_order = None
			self.sale_order_date = None

	def validate_sales_order(self):
		if self.party_type == "Customer" and self.sales_order:
			so = frappe.db.get_value(
				"Sales Order",
				self.sales_order,
				["customer", "status", "transaction_date"],
				as_dict=True
			)
			if so:
				if so.customer != self.customer:
					frappe.throw(_("Sales Order {0} does not belong to Customer {1}").format(
						self.sales_order, self.customer
					))
				if so.status == "Completed":
					frappe.throw(_("Sales Order {0} cannot be selected because its status is Completed").format(
						self.sales_order
					))
				if not self.sale_order_date:
					self.sale_order_date = so.transaction_date

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
