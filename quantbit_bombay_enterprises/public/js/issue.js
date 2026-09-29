// Copyright (c) 2026, Quantbit Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Issue", {
	refresh: function (frm) {
		if (frm.doc.status !== "Closed") {
			frm.add_custom_button(
				__("Quotation"),
				function () {
					frappe.model.open_mapped_doc({
						method: "quantbit_bombay_enterprises.public.python.issue.make_quotation",
						frm: frm,
					});
				},
				__("Create")
			);

			frm.add_custom_button(
				__("Material Inward"),
				function () {
					frappe.model.open_mapped_doc({
						method: "quantbit_bombay_enterprises.public.python.issue.make_material_inward",
						frm: frm,
					});
				},
				__("Create")
			);
		}
	},
});
