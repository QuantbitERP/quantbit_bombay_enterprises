frappe.ui.form.on('Delivery Note', {
  refresh(frm) {
    // juna saved draft: current SO lakshat theva, data badlu naka
    if (!frm.is_new() && frm.__last_so === undefined) {
      get_first_so(frm).then(so => { frm.__last_so = so || ''; });
      return;
    }
    setTimeout(() => fetch_transporter_from_so(frm), 500);
  },
  items_add(frm) {
    setTimeout(() => fetch_transporter_from_so(frm), 500);
  },
  items_remove(frm) {
    setTimeout(() => fetch_transporter_from_so(frm), 500);
  }
});

frappe.ui.form.on('Delivery Note Item', {
  against_sales_order(frm) {
    setTimeout(() => fetch_transporter_from_so(frm), 300);
  }
});

// Sales Order shodha: 1) against_sales_order  2) Pick List  3) so_detail
function get_first_so(frm) {
  const row = (frm.doc.items || [])[0];
  if (!row) return Promise.resolve('');

  if (row.against_sales_order) return Promise.resolve(row.against_sales_order);

  if (row.against_pick_list) {
    return frappe.call({
      method: 'frappe.client.get',
      args: { doctype: 'Pick List', name: row.against_pick_list }
    }).then(r => {
      const pl = r.message;
      if (!pl) return '';
      const locs = pl.locations || [];
      const loc = locs.find(l => l.name === row.pick_list_item && l.sales_order)
        || locs.find(l => l.sales_order);
      return loc ? loc.sales_order : (pl.sales_order || '');
    });
  }

  if (row.so_detail) {
    return frappe.call({
      method: 'frappe.client.get_list',
      args: {
        doctype: 'Sales Order Item',
        parent: 'Sales Order',
        filters: { name: row.so_detail },
        fields: ['parent'],
        limit_page_length: 1
      }
    }).then(r => (r.message && r.message[0]) ? r.message[0].parent : '');
  }

  return Promise.resolve('');
}

function fetch_transporter_from_so(frm) {
  if (frm.doc.docstatus !== 0 || frm.__busy) return;
  frm.__busy = true;

  get_first_so(frm).then(so_name => {
    if (!so_name || so_name === frm.__last_so) { frm.__busy = false; return; }

    frappe.call({
      method: 'frappe.client.get',
      args: { doctype: 'Sales Order', name: so_name },
      callback(r) {
        frm.__busy = false;
        const so = r.message;
        if (!so) return;
        frm.__last_so = so_name;

        const gst_id = so.custom_gst_transporter_id
          || so.custom_gst_transporters_id
          || so.custom_gst_taransporters_id || '';

        const values = {
          transporter: so.custom_transporter,
          transporter_name: so.custom_transporter_name,
          gst_transporter_id: gst_id,
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
          gst_vehicle_type: so.custom_gst_vehicle_type,
          custom_remark: so.custom_remark
        };

        const apply = () => {
          Object.keys(values).forEach(f => {
            if (values[f] && frm.fields_dict[f]) {
              frappe.model.set_value(frm.doctype, frm.docname, f, values[f]);
            }
          });
        };
        apply();
        // transporter set kelyavar standard fetch value ovrite karu shakto, mhanun parat
        setTimeout(apply, 1000);

        frappe.show_alert({
          message: so.custom_transporter
            ? 'Transporter info ' + so_name + ' madhun ghetli'
            : so_name + ' madhe Transporter info bharlela nahi',
          indicator: so.custom_transporter ? 'green' : 'orange'
        });
      },
      error() { frm.__busy = false; }
    });
  });
}