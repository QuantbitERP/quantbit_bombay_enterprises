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
	onload(frm) {
		if (!frm.is_new() || frm.doc.transporter) return;
		const row = (frm.doc.items || []).find(r => r.delivery_note);
		if (!row) return;

		frappe.db.get_value('Delivery Note', row.delivery_note, [
		'transporter', 'gst_transporter_id', 'transporter_name',
		'driver', 'driver_name', 'custom_driver__name',
		'lr_no', 'lr_date',
		'vehicle_no', 'custom_vehicle__no',
		'distance', 'custom_distance_in_km',
		'mode_of_transport', 'gst_vehicle_type',
		'custom_no_of_packages','custom_remark'
		]).then(({ message: dn }) => {
		if (!dn) return;
		const vals = {
			transporter: dn.transporter,
			gst_transporter_id: dn.gst_transporter_id,
			transporter_name: dn.transporter_name,
			driver: dn.driver,
			driver_name: dn.driver_name || dn.custom_driver__name,
			lr_no: dn.lr_no,
			lr_date: dn.lr_date,
			vehicle_no: dn.vehicle_no || dn.custom_vehicle__no,
			distance: dn.distance || dn.custom_distance_in_km,
			mode_of_transport: dn.mode_of_transport,
			gst_vehicle_type: dn.gst_vehicle_type,
			custom_no_of_packages: dn.custom_no_of_packages,
			remark : den.custom_remark
		};
		Object.keys(vals).forEach(k => { if (!vals[k]) delete vals[k]; });
		frm.set_value(vals);
		});
	}

});
