// Copyright (c) 2026, Quantbit Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Material Inward", {
	setup: function(frm) {
		frm.set_query("sales_order", function() {
			return {
				filters: [
					["Sales Order", "customer", "=", frm.doc.customer || ""],
					["Sales Order", "status", "!=", "Completed"],
					["Sales Order", "docstatus", "=", 1]
				]
			};
		});
	},

	onload: function(frm) {
		if (frm.is_new() && !frm.doc.company) {
			let default_company = frappe.defaults.get_user_default("Company") || frappe.defaults.get_default("company");
			if (default_company) {
				frm.set_value("company", default_company);
			}
		}
		if (frm.is_new() && !frm.doc.party_type) {
			frm.set_value("party_type", "Customer");
		}
	},

	refresh: function(frm) {
		calculate_total_quantity(frm);
	},

	party_type: function(frm) {
		if (frm.doc.party_type === "Customer") {
			frm.set_value("supplier", "");
			frm.set_value("supplier_name", "");
		} else if (frm.doc.party_type === "Supplier") {
			frm.set_value("customer", "");
			frm.set_value("customer_name", "");
			frm.set_value("sales_order", "");
			frm.set_value("sale_order_date", "");
		}
	},

	customer: function(frm) {
		frm.set_value("sales_order", "");
		frm.set_value("sale_order_date", "");
	},

	sales_order: function(frm) {
		if (frm.doc.sales_order) {
			frappe.db.get_value("Sales Order", frm.doc.sales_order, "transaction_date", function(r) {
				if (r && r.transaction_date) {
					frm.set_value("sale_order_date", r.transaction_date);
				}
			});
		} else {
			frm.set_value("sale_order_date", "");
		}
	}
});

frappe.ui.form.on("Material Inward Item", {
	item: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (row.item) {
			frappe.db.get_value("Item", row.item, ["item_name", "description", "stock_uom"], function(r) {
				if (r) {
					frappe.model.set_value(cdt, cdn, "item_name", r.item_name || "");
					frappe.model.set_value(cdt, cdn, "description", r.description || "");
					frappe.model.set_value(cdt, cdn, "uom", r.stock_uom || "");
				}
			});
		}
	},

	quantity: function(frm, cdt, cdn) {
		calculate_total_quantity(frm);
	},

	items_remove: function(frm) {
		calculate_total_quantity(frm);
	}
});

function calculate_total_quantity(frm) {
	let total = 0.0;
	(frm.doc.items || []).forEach(function(row) {
		total += flt(row.quantity);
	});
	frm.set_value("total_quantity", total);
}
