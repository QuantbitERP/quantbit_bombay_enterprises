// Copyright (c) 2026, Quantbit Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Pricing Rule Tool", {
	setup: function (frm) {
		frm.fields_dict["for_price_list"].get_query = function (doc) {
			return {
				filters: {
					selling: 1,
					currency: doc.currency,
				},
			};
		};

		["items", "item_groups", "brands"].forEach((d) => {
			if (frm.fields_dict[d]) {
				frm.fields_dict[d].grid.get_field("uom").get_query = function (doc, cdt, cdn) {
					var row = locals[cdt][cdn];
					return {
						query: "erpnext.accounts.doctype.pricing_rule.pricing_rule.get_item_uoms",
						filters: { value: row[frappe.scrub(doc.apply_on)], apply_on: doc.apply_on },
					};
				};
			}
		});
	},

	onload: function (frm) {
		if (frm.is_new() && !frm.doc.currency && frm.doc.company) {
			frm.trigger("company");
		}
	},

	refresh: function (frm) {
		if (frm.doc.docstatus === 1) {
			frm.add_custom_button(__("View Pricing Rules"), function () {
				frappe.route_options = {
					title: frm.doc.title,
				};
				frappe.set_route("List", "Pricing Rule");
			}, __("Actions"));
		}
	},

	company: function (frm) {
		if (frm.doc.company) {
			frappe.db.get_value("Company", frm.doc.company, "default_currency", function (r) {
				if (r && r.default_currency) {
					frm.set_value("currency", r.default_currency);
				}
			});
		}
	},

	apply_on: function (frm) {
		if (frm.doc.apply_on === "Transaction") {
			frm.set_value("price_or_product_discount", "Price");
		}
	},

	price_or_product_discount: function (frm) {
		if (frm.doc.price_or_product_discount === "Product") {
			frm.set_value("rate_or_discount", "Discount Percentage");
		}
	},
});

frappe.ui.form.on("Pricing Rule Tool Customer", {
	form_render: function (frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		let grid_row = frm.fields_dict.customers && frm.fields_dict.customers.grid.get_row(cdn);
		if (grid_row && grid_row.grid_form) {
			let field = grid_row.grid_form.fields_dict.pricing_rule;
			if (field && field.$input) {
				if (!row.pricing_rule) {
					field.$input.prop("disabled", true);
					field.$input.attr("placeholder", __("Auto-generated on Submit"));
				} else {
					field.$input.prop("disabled", false);
				}
			}
		}
	},

	customer: function (frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (row.customer) {
			frappe.db.get_value("Customer", row.customer, "customer_name", function (r) {
				if (r && r.customer_name) {
					frappe.model.set_value(cdt, cdn, "customer_name", r.customer_name);
				}
			});
		} else {
			frappe.model.set_value(cdt, cdn, "customer_name", "");
		}
	},
});
