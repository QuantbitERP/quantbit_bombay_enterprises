// Copyright (c) 2026, Quantbit Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Sales Invoice", {
	refresh: function (frm) {
		if (!frm.is_new() && !frm.doc.is_return) {
			frm.add_custom_button(
				__("Material Outward"),
				function () {
					frappe.model.open_mapped_doc({
						method: "quantbit_bombay_enterprises.public.python.sales_invoice.make_material_outward",
						frm: frm,
					});
				},
				__("Create")
			);
		}
	},
});
