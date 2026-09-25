# Copyright (c) 2026, Quantbit Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, get_link_to_form


class PricingRuleTool(Document):
	def validate(self):
		self.validate_customers()
		self.validate_mandatory_items()
		self.validate_dates_and_amounts()

	def validate_customers(self):
		if not self.customers:
			frappe.throw(_("Please add at least one Customer in the Customers table."))

		seen_customers = set()
		for row in self.customers:
			if not row.customer:
				frappe.throw(_("Row #{0}: Customer is required.").format(row.idx))
			if row.customer in seen_customers:
				frappe.throw(
					_("Row #{0}: Customer {1} is added multiple times.").format(
						row.idx, frappe.bold(row.customer)
					)
				)
			seen_customers.add(row.customer)

	def validate_mandatory_items(self):
		if self.apply_on == "Item Code" and not self.items:
			frappe.throw(_("Please add at least one Item in the Item Code table."))
		elif self.apply_on == "Item Group" and not self.item_groups:
			frappe.throw(_("Please add at least one Item Group in the Item Group table."))
		elif self.apply_on == "Brand" and not self.brands:
			frappe.throw(_("Please add at least one Brand in the Brand table."))

	def validate_dates_and_amounts(self):
		if self.valid_from and self.valid_upto and str(self.valid_upto) < str(self.valid_from):
			frappe.throw(_("Valid Up To date cannot be earlier than Valid From date."))

		if self.min_qty and self.max_qty and flt(self.min_qty) > flt(self.max_qty):
			frappe.throw(_("Max Qty cannot be less than Min Qty."))

		if self.min_amt and self.max_amt and flt(self.min_amt) > flt(self.max_amt):
			frappe.throw(_("Max Amt cannot be less than Min Amt."))

	def on_submit(self):
		self.create_pricing_rules()

	def create_pricing_rules(self):
		fields_to_copy = [
			"disable",
			"apply_on",
			"price_or_product_discount",
			"warehouse",
			"mixed_conditions",
			"is_cumulative",
			"coupon_code_based",
			"apply_rule_on_other",
			"other_item_code",
			"other_item_group",
			"other_brand",
			"min_qty",
			"max_qty",
			"min_amt",
			"max_amt",
			"valid_from",
			"valid_upto",
			"company",
			"currency",
			"margin_type",
			"margin_rate_or_amount",
			"rate_or_discount",
			"apply_discount_on",
			"rate",
			"discount_amount",
			"discount_percentage",
			"for_price_list",
			"same_item",
			"free_item",
			"free_qty",
			"free_item_uom",
			"free_item_rate",
			"round_free_qty",
			"dont_enforce_free_item_qty",
			"is_recursive",
			"recurse_for",
			"apply_recursion_over",
			"condition",
			"apply_multiple_pricing_rules",
			"apply_discount_on_rate",
			"threshold_percentage",
			"validate_applied_rule",
			"rule_description",
			"has_priority",
			"priority",
		]

		created_rules = []

		for row in self.customers:
			pr = frappe.new_doc("Pricing Rule")

			for field in fields_to_copy:
				val = self.get(field)
				if val is not None:
					pr.set(field, val)

			pr.title = self.title
			pr.selling = 1
			pr.buying = 0
			pr.applicable_for = "Customer"
			pr.customer = row.customer

			if self.apply_on == "Item Code":
				for item in self.items:
					pr.append("items", {
						"item_code": item.item_code,
						"uom": item.uom,
					})
			elif self.apply_on == "Item Group":
				for ig in self.item_groups:
					pr.append("item_groups", {
						"item_group": ig.item_group,
						"uom": ig.uom,
					})
			elif self.apply_on == "Brand":
				for b in self.brands:
					pr.append("brands", {
						"brand": b.brand,
						"uom": b.uom,
					})

			pr.insert(ignore_permissions=True)

			row.pricing_rule = pr.name
			frappe.db.set_value(row.doctype, row.name, "pricing_rule", pr.name)

			created_rules.append(f"{get_link_to_form('Pricing Rule', pr.name)} ({frappe.bold(row.customer)})")

		if created_rules:
			frappe.msgprint(
				_("Successfully created Pricing Rules for all customers:<br>{0}").format("<br>".join(created_rules)),
				title=_("Pricing Rules Generated"),
				indicator="green",
			)

	def on_cancel(self):
		disabled_rules = []
		for row in self.customers:
			if row.pricing_rule and frappe.db.exists("Pricing Rule", row.pricing_rule):
				frappe.db.set_value("Pricing Rule", row.pricing_rule, "disable", 1)
				disabled_rules.append(get_link_to_form("Pricing Rule", row.pricing_rule))

		if disabled_rules:
			frappe.msgprint(
				_("Disabled the following associated Pricing Rules:<br>{0}").format("<br>".join(disabled_rules)),
				title=_("Pricing Rules Disabled"),
				indicator="orange",
			)
