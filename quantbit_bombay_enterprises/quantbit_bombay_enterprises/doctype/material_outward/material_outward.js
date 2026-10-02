// Copyright (c) 2026, Quantbit Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Material Outward", {
	setup: function(frm) {
		frm.set_query("against_document", function() {
			let filters = {
				docstatus: ["<", 2]
			};
			if (frm.doc.party_type) {
				filters["party_type"] = frm.doc.party_type;
			}
			if (frm.doc.party_type === "Customer" && frm.doc.customer) {
				filters["customer"] = frm.doc.customer;
			} else if (frm.doc.party_type === "Supplier" && frm.doc.supplier) {
				filters["supplier"] = frm.doc.supplier;
			}
			if (frm.doc.company) {
				filters["company"] = frm.doc.company;
			}
			return { filters: filters };
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
		frm.set_value("against_document", "");
		frm.set_value("party_receipt_no", "");
		frm.clear_table("items");
		frm.refresh_field("items");
		calculate_total_quantity(frm);

		if (frm.doc.party_type === "Customer") {
			frm.set_value("supplier", "");
			frm.set_value("supplier_name", "");
		} else if (frm.doc.party_type === "Supplier") {
			frm.set_value("customer", "");
			frm.set_value("customer_name", "");
		}
	},

	customer: function(frm) {
		frm.set_value("against_document", "");
		frm.set_value("party_receipt_no", "");
		frm.clear_table("items");
		frm.refresh_field("items");
		calculate_total_quantity(frm);
	},

	supplier: function(frm) {
		frm.set_value("against_document", "");
		frm.set_value("party_receipt_no", "");
		frm.clear_table("items");
		frm.refresh_field("items");
		calculate_total_quantity(frm);
	},

	against_document: function(frm) {
		if (!frm.doc.against_document) {
			frm.set_value("party_receipt_no", "");
			return;
		}

		frappe.call({
			method: "quantbit_bombay_enterprises.quantbit_bombay_enterprises.doctype.material_outward.material_outward.get_inward_details",
			args: {
				inward_name: frm.doc.against_document
			},
			callback: function(r) {
				if (r && r.message) {
					let data = r.message;
					if (data.party_type) {
						frm.set_value("party_type", data.party_type);
					}
					if (data.party_type === "Customer" && data.customer) {
						frm.set_value("customer", data.customer);
						frm.set_value("customer_name", data.customer_name || "");
					} else if (data.party_type === "Supplier" && data.supplier) {
						frm.set_value("supplier", data.supplier);
						frm.set_value("supplier_name", data.supplier_name || "");
					}
					if (data.company && !frm.doc.company) {
						frm.set_value("company", data.company);
					}

					frm.set_value("party_receipt_no", data.party_receipt_no || "");

					frm.clear_table("items");
					(data.items || []).forEach(function(item) {
						let row = frm.add_child("items");
						row.item = item.item;
						row.item_name = item.item_name;
						row.description = item.description;
						row.uom = item.uom;
						row.quantity = item.quantity;
						row.inward_item = item.inward_item;
					});
					frm.refresh_field("items");
					calculate_total_quantity(frm);
				}
			}
		});
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
