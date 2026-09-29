# Copyright (c) 2026, Quantbit Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase
from frappe.utils import flt
from quantbit_bombay_enterprises.sales_invoice import make_material_outward


class UnitTestMaterialOutward(UnitTestCase):
	pass


class TestMaterialOutward(IntegrationTestCase):
	def test_make_material_outward_from_sales_invoice(self):
		si_name = "ACC-SINV-2026-00004"
		if not frappe.db.exists("Sales Invoice", si_name):
			si_name = frappe.db.get_value("Sales Invoice", {"docstatus": 1})

		self.assertTrue(si_name, "Sales Invoice must exist for testing")
		si = frappe.get_doc("Sales Invoice", si_name)

		mo = make_material_outward(si.name)
		self.assertEqual(mo.doctype, "Material Outward")
		self.assertEqual(mo.customer, si.customer)
		self.assertEqual(mo.customer_name, si.customer_name)
		self.assertEqual(mo.company, si.company)
		self.assertEqual(mo.party_type, "Customer")
		self.assertEqual(mo.sales_invoice, si.name)
		self.assertEqual(len(mo.items), len(si.items))

		expected_qty = sum(flt(item.qty) for item in si.items)
		self.assertEqual(flt(mo.total_quantity), expected_qty)

		# Test insert
		mo.insert(ignore_permissions=True)
		self.assertTrue(mo.name)

		# Verify Sales Invoice dashboard contains Material Outward
		meta = frappe.get_meta("Sales Invoice")
		dashboard_data = meta.get_dashboard_data()
		all_items = []
		for group in dashboard_data.get("transactions", []):
			all_items.extend(group.get("items", []))
		self.assertIn("Material Outward", all_items)

		# Clean up
		frappe.delete_doc("Material Outward", mo.name, force=1)
		frappe.db.commit()


def run():
	t = TestMaterialOutward("test_make_material_outward_from_sales_invoice")
	t.test_make_material_outward_from_sales_invoice()
	print("Material Outward from Sales Invoice test executed successfully!")
