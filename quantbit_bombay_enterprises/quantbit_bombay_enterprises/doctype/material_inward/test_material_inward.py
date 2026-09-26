# Copyright (c) 2026, Quantbit Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase
from frappe.utils import today, flt
from quantbit_bombay_enterprises.quantbit_bombay_enterprises.doctype.material_outward.material_outward import get_inward_details
from quantbit_bombay_enterprises.quantbit_bombay_enterprises.report.material_inward_outward_report.material_inward_outward_report import execute


class UnitTestMaterialInward(UnitTestCase):
	pass


class TestMaterialInward(IntegrationTestCase):
	def test_material_inward_and_outward_flow(self):
		company = frappe.db.get_value("Company", {}, "name")
		customer = frappe.db.get_value("Customer", {}, "name")
		customer_name = frappe.db.get_value("Customer", customer, "customer_name")
		supplier = frappe.db.get_value("Supplier", {}, "name")
		supplier_name = frappe.db.get_value("Supplier", supplier, "supplier_name")
		item = frappe.db.get_value("Item", {}, "name")

		# 1. Create Inward for Customer
		inw_customer = frappe.get_doc({
			"doctype": "Material Inward",
			"company": company,
			"posting_date": today(),
			"party_type": "Customer",
			"customer": customer,
			"party_receipt_no": "REC-INW-001",
			"remarks": "Inward testing for customer",
			"items": [
				{
					"item": item,
					"quantity": 100.0
				}
			]
		})
		inw_customer.insert(ignore_permissions=True)
		self.assertTrue(inw_customer.name)
		self.assertEqual(inw_customer.customer_name, customer_name)
		self.assertEqual(flt(inw_customer.total_quantity), 100.0)
		self.assertTrue(inw_customer.items[0].item_name)
		self.assertTrue(inw_customer.items[0].uom)

		# 2. Test get_inward_details API
		details = get_inward_details(inw_customer.name)
		self.assertEqual(details["party_type"], "Customer")
		self.assertEqual(details["customer"], customer)
		self.assertEqual(details["party_receipt_no"], "REC-INW-001")
		self.assertEqual(len(details["items"]), 1)
		self.assertEqual(flt(details["items"][0]["quantity"]), 100.0)

		# 3. Create Outward against Customer Inward
		outw_customer = frappe.get_doc({
			"doctype": "Material Outward",
			"company": company,
			"posting_date": today(),
			"party_type": "Customer",
			"customer": customer,
			"against_document": inw_customer.name,
			"party_receipt_no": details["party_receipt_no"],
			"remarks": "Outward testing for customer",
			"items": [
				{
					"item": details["items"][0]["item"],
					"item_name": details["items"][0]["item_name"],
					"description": details["items"][0]["description"],
					"uom": details["items"][0]["uom"],
					"quantity": 40.0,
					"inward_item": details["items"][0]["inward_item"]
				}
			]
		})
		outw_customer.insert(ignore_permissions=True)
		self.assertTrue(outw_customer.name)
		self.assertEqual(outw_customer.party_receipt_no, "REC-INW-001")
		self.assertEqual(flt(outw_customer.total_quantity), 40.0)

		# 4. Create Inward for Supplier
		inw_supplier = frappe.get_doc({
			"doctype": "Material Inward",
			"company": company,
			"posting_date": today(),
			"party_type": "Supplier",
			"supplier": supplier,
			"party_receipt_no": "REC-INW-SUP-001",
			"remarks": "Inward testing for supplier",
			"items": [
				{
					"item": item,
					"quantity": 60.0
				}
			]
		})
		inw_supplier.insert(ignore_permissions=True)
		self.assertTrue(inw_supplier.name)
		self.assertEqual(inw_supplier.supplier_name, supplier_name)
		self.assertEqual(flt(inw_supplier.total_quantity), 60.0)

		# 5. Test Report Execution
		cols, data = execute({"company": company})
		col_labels = [c["label"] for c in cols]
		expected_labels = [
			"Inward Date",
			"Party Type",
			"Party",
			"Party Name",
			"Item Name",
			"Inward Quantity",
			"Outward date",
			"Outward Quantity",
			"Balance Quantiy"
		]
		for exp in expected_labels:
			self.assertIn(exp, col_labels)

		# Check Customer Inward row in report
		cust_rows = [r for r in data if r.get("party") == customer and r.get("item_name") == inw_customer.items[0].item_name]
		self.assertTrue(len(cust_rows) >= 1)
		first_row = cust_rows[0]
		self.assertEqual(flt(first_row["inward_quantity"]), 100.0)
		self.assertEqual(flt(first_row["outward_quantity"]), 40.0)
		self.assertEqual(flt(first_row["balance_quantity"]), 60.0)

		# Cleanup test data
		frappe.delete_doc("Material Outward", outw_customer.name, force=1)
		frappe.delete_doc("Material Inward", inw_customer.name, force=1)
		frappe.delete_doc("Material Inward", inw_supplier.name, force=1)
		frappe.db.commit()


def run():
	t = TestMaterialInward()
	t.test_material_inward_and_outward_flow()
	print("Material Inward and Outward tests executed successfully!")
