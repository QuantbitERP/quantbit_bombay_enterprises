frappe.ui.form.on('Delivery Note', {
  onload(frm) {
    if (!frm.is_new() || frm.doc.transporter) return;
    const row = (frm.doc.items || []).find(r => r.against_sales_order);
    if (!row) return;

    frappe.db.get_value('Sales Order', row.against_sales_order, [
      'custom_transporter', 'custom_gst_transporter_id', 'custom_gst_transporters_id',
      'custom_transporter_name', 'custom_driver', 'custom_driver_name',
      'custom_transport_receipt_no', 'custom_transport_receipt_date',
      'custom_vehicle_no', 'custom_distance_in_km', 'custom_no_of_packages',
      'custom_mode__of_transport', 'custom_gst_vehicle_type'
    ]).then(({ message: so }) => {
      if (!so) return;
      const vals = {
        transporter: so.custom_transporter,
        gst_transporter_id: so.custom_gst_transporter_id || so.custom_gst_transporters_id,
        transporter_name: so.custom_transporter_name,
        driver: so.custom_driver,
        driver_name: so.custom_driver_name,
        custom_driver__name: so.custom_driver_name,
        lr_no: so.custom_transport_receipt_no,
        lr_date: so.custom_transport_receipt_date,
        vehicle_no: so.custom_vehicle_no,
        custom_vehicle__no: so.custom_vehicle_no,
        distance: so.custom_distance_in_km,
        custom_distance_in_km: so.custom_distance_in_km,
        custom_no_of_packages: so.custom_no_of_packages,
        mode_of_transport: so.custom_mode__of_transport,
        gst_vehicle_type: so.custom_gst_vehicle_type
      };
      Object.keys(vals).forEach(k => { if (!vals[k]) delete vals[k]; });
      frm.set_value(vals);
    });
  }
});