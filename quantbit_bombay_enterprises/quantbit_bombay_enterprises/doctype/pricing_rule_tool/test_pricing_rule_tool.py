# Copyright (c) 2026, Quantbit Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase


class UnitTestPricingRuleTool(UnitTestCase):
	"""
	Unit tests for PricingRuleTool.
	Use this class for testing individual functions and methods.
	"""

	pass


class TestPricingRuleTool(IntegrationTestCase):
	def test_pricing_rule_tool_creation_and_submission(self):
		cg = frappe.db.get_value("Customer Group", {"is_group": 0}, "name") or "Individual"
		cust_names = []
		for cust_id in ["TEST-CUST-PRT-1", "TEST-CUST-PRT-2"]:
			c = frappe.get_doc({
				"doctype": "Customer",
				"customer_name": f"Test Customer {cust_id}",
				"customer_type": "Company",
				"customer_group": cg,
				"territory": "All Territories"
			})
			c.insert(ignore_permissions=True)
			cust_names.append(c.name)

		item_code = "TEST-ITEM-PRT"
		if not frappe.db.exists("Item", item_code):
			item = frappe.get_doc({
				"doctype": "Item",
				"item_code": item_code,
				"item_name": "Test Item PRT",
				"item_group": "All Item Groups",
				"stock_uom": "Nos",
				"is_stock_item": 0
			})
			item.insert(ignore_permissions=True)

		company = frappe.db.get_value("Company", {}, "name")
		currency = frappe.db.get_value("Company", company, "default_currency") or "INR"

		tool = frappe.get_doc({
			"doctype": "Pricing Rule Tool",
			"title": "Special Discount 2026",
			"apply_on": "Item Code",
			"price_or_product_discount": "Price",
			"rate_or_discount": "Discount Percentage",
			"discount_percentage": 20.0,
			"company": company,
			"currency": currency,
			"items": [
				{
					"item_code": item_code,
					"uom": "Nos"
				}
			],
			"customers": [
				{
					"customer": cust_names[0]
				},
				{
					"customer": cust_names[1]
				}
			]
		})
		tool.insert(ignore_permissions=True)
		self.assertTrue(tool.name)

		# Submit tool
		tool.submit()

		tool.reload()
		for row in tool.customers:
			self.assertTrue(row.pricing_rule)
			pr = frappe.get_doc("Pricing Rule", row.pricing_rule)
			self.assertEqual(pr.title, tool.title)
			self.assertEqual(pr.customer, row.customer)
			self.assertEqual(pr.selling, 1)
			self.assertEqual(pr.buying, 0)
			self.assertEqual(pr.applicable_for, "Customer")
			self.assertEqual(pr.discount_percentage, 20.0)
			self.assertEqual(pr.disable, 0)
			self.assertEqual(len(pr.items), 1)
			self.assertEqual(pr.items[0].item_code, item_code)

		# Test Cancel
		tool.cancel()
		tool.reload()
		for row in tool.customers:
			pr = frappe.get_doc("Pricing Rule", row.pricing_rule)
			self.assertEqual(pr.disable, 1)

		# Cleanup
		for row in tool.customers:
			frappe.delete_doc("Pricing Rule", row.pricing_rule, force=1)
		frappe.delete_doc("Pricing Rule Tool", tool.name, force=1)
		for c_name in cust_names:
			frappe.delete_doc("Customer", c_name, force=1)


def run():
	t = TestPricingRuleTool()
	t.test_pricing_rule_tool_creation_and_submission()
	print("Pricing Rule Tool test executed successfully!")
