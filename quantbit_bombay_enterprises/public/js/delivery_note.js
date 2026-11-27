// frappe.ui.form.on('Delivery Note', {
//   refresh(frm) {
//     // juna saved draft: current SO lakshat theva, data badlu naka
//     if (!frm.is_new() && frm.__last_so === undefined) {
//       get_first_so(frm).then(so => { frm.__last_so = so || ''; });
//       return;
//     }
//     setTimeout(() => fetch_transporter_from_so(frm), 500);
//   },
//   items_add(frm) {
//     setTimeout(() => fetch_transporter_from_so(frm), 500);
//   },
//   items_remove(frm) {
//     setTimeout(() => fetch_transporter_from_so(frm), 500);
//   }
// });

// frappe.ui.form.on('Delivery Note Item', {
//   against_sales_order(frm) {
//     setTimeout(() => fetch_transporter_from_so(frm), 300);
//   }
// });

// // Sales Order shodha: 1) against_sales_order  2) Pick List  3) so_detail
// function get_first_so(frm) {
//   const row = (frm.doc.items || [])[0];
//   if (!row) return Promise.resolve('');

//   if (row.against_sales_order) return Promise.resolve(row.against_sales_order);

//   if (row.against_pick_list) {
//     return frappe.call({
//       method: 'frappe.client.get',
//       args: { doctype: 'Pick List', name: row.against_pick_list }
//     }).then(r => {
//       const pl = r.message;
//       if (!pl) return '';
//       const locs = pl.locations || [];
//       const loc = locs.find(l => l.name === row.pick_list_item && l.sales_order)
//         || locs.find(l => l.sales_order);
//       return loc ? loc.sales_order : (pl.sales_order || '');
//     });
//   }

//   if (row.so_detail) {
//     return frappe.call({
//       method: 'frappe.client.get_list',
//       args: {
//         doctype: 'Sales Order Item',
//         parent: 'Sales Order',
//         filters: { name: row.so_detail },
//         fields: ['parent'],
//         limit_page_length: 1
//       }
//     }).then(r => (r.message && r.message[0]) ? r.message[0].parent : '');
//   }

//   return Promise.resolve('');
// }

// function fetch_transporter_from_so(frm) {
//   if (frm.doc.docstatus !== 0 || frm.__busy) return;
//   frm.__busy = true;

//   get_first_so(frm).then(so_name => {
//     if (!so_name || so_name === frm.__last_so) { frm.__busy = false; return; }

//     frappe.call({
//       method: 'frappe.client.get',
//       args: { doctype: 'Sales Order', name: so_name },
//       callback(r) {
//         frm.__busy = false;
//         const so = r.message;
//         if (!so) return;
//         frm.__last_so = so_name;

//         const gst_id = so.custom_gst_transporter_id
//           || so.custom_gst_transporters_id
//           || so.custom_gst_taransporters_id || '';

//         const values = {
//           transporter: so.custom_transporter,
//           transporter_name: so.custom_transporter_name,
//           gst_transporter_id: gst_id,
//           driver: so.custom_driver,
//           driver_name: so.custom_driver_name,
//           custom_driver__name: so.custom_driver_name,
//           lr_no: so.custom_transport_receipt_no,
//           lr_date: so.custom_transport_receipt_date,
//           vehicle_no: so.custom_vehicle_no,
//           custom_vehicle__no: so.custom_vehicle_no,
//           distance: so.custom_distance_in_km,
//           custom_distance_in_km: so.custom_distance_in_km,
//           custom_no_of_packages: so.custom_no_of_packages,
//           mode_of_transport: so.custom_mode__of_transport,
//           gst_vehicle_type: so.custom_gst_vehicle_type,
//           custom_remark: so.custom_remark
//         };

//         const apply = () => {
//           Object.keys(values).forEach(f => {
//             if (values[f] && frm.fields_dict[f]) {
//               frappe.model.set_value(frm.doctype, frm.docname, f, values[f]);
//             }
//           });
//         };
//         apply();
//         // transporter set kelyavar standard fetch value ovrite karu shakto, mhanun parat
//         setTimeout(apply, 1000);

//         frappe.show_alert({
//           message: so.custom_transporter
//             ? 'Transporter info ' + so_name + ' madhun ghetli'
//             : so_name + ' madhe Transporter info bharlela nahi',
//           indicator: so.custom_transporter ? 'green' : 'orange'
//         });
//       },
//       error() { frm.__busy = false; }
//     });
//   });
// }


frappe.ui.form.on('Delivery Note', {
  refresh(frm) {
    // Every time a draft Delivery Note is opened
    if (frm.doc.docstatus === 0) {
      setTimeout(() => {
        sync_transporter_from_sales_order(frm);
      }, 500);
    }
  },

  items_add(frm) {
    setTimeout(() => sync_transporter_from_sales_order(frm), 500);
  },

  items_remove(frm) {
    setTimeout(() => sync_transporter_from_sales_order(frm), 500);
  }
});

frappe.ui.form.on('Delivery Note Item', {
  against_sales_order(frm) {
    setTimeout(() => sync_transporter_from_sales_order(frm), 300);
  },

  against_pick_list(frm) {
    setTimeout(() => sync_transporter_from_sales_order(frm), 300);
  },

  pick_list_item(frm) {
    setTimeout(() => sync_transporter_from_sales_order(frm), 300);
  }
});


// ==========================================
// GET SALES ORDER FROM DELIVERY NOTE ITEM
// Priority:
// 1. against_sales_order
// 2. Pick List
// 3. so_detail
// ==========================================

async function get_delivery_sales_order(frm) {

  const row = (frm.doc.items || []).find(d =>
    d.against_sales_order ||
    d.against_pick_list ||
    d.so_detail
  );

  if (!row) return '';

  // Direct Sales Order link
  if (row.against_sales_order) {
    return row.against_sales_order;
  }

  // Find Sales Order from Pick List
  if (row.against_pick_list) {

    const r = await frappe.call({
      method: 'frappe.client.get',
      args: {
        doctype: 'Pick List',
        name: row.against_pick_list
      }
    });

    const pl = r.message;

    if (pl) {
      const locations = pl.locations || [];

      const location = locations.find(l =>
        l.name === row.pick_list_item && l.sales_order
      ) || locations.find(l => l.sales_order);

      if (location && location.sales_order) {
        return location.sales_order;
      }

      if (pl.sales_order) {
        return pl.sales_order;
      }
    }
  }

  // Find Sales Order using SO Detail
  if (row.so_detail) {

    const r = await frappe.call({
      method: 'frappe.client.get_list',
      args: {
        doctype: 'Sales Order Item',
        filters: {
          name: row.so_detail
        },
        fields: ['parent'],
        limit_page_length: 1
      }
    });

    if (r.message && r.message.length) {
      return r.message[0].parent;
    }
  }

  return '';
}


// ==========================================
// FETCH AND SYNC TRANSPORTER INFORMATION
// ==========================================

async function sync_transporter_from_sales_order(frm) {

  // Only Draft Delivery Note
  if (frm.doc.docstatus !== 0) return;

  // Prevent multiple simultaneous requests
  if (frm.__transporter_sync_running) return;

  frm.__transporter_sync_running = true;

  try {

    const so_name = await get_delivery_sales_order(frm);

    if (!so_name) {
      return;
    }

    // Get complete Sales Order
    const response = await frappe.call({
      method: 'frappe.client.get',
      args: {
        doctype: 'Sales Order',
        name: so_name
      }
    });

    const so = response.message;

    if (!so) return;

    // GST Transporter ID
    const gst_id =
      so.custom_gst_transporter_id ||
      so.custom_gst_transporters_id ||
      so.custom_gst_taransporters_id ||
      '';

    // Sales Order to Delivery Note field mapping
    const values = {

      transporter: so.custom_transporter || '',

      transporter_name: so.custom_transporter_name || '',

      gst_transporter_id: gst_id,

      driver: so.custom_driver || '',

      driver_name: so.custom_driver_name || '',

      custom_driver__name: so.custom_driver_name || '',

      lr_no: so.custom_transport_receipt_no || '',

      lr_date: so.custom_transport_receipt_date || '',

      vehicle_no: so.custom_vehicle_no || '',

      custom_vehicle__no: so.custom_vehicle_no || '',

      distance: so.custom_distance_in_km || 0,

      custom_distance_in_km: so.custom_distance_in_km || 0,

      custom_no_of_packages: so.custom_no_of_packages || 0,

      mode_of_transport: so.custom_mode__of_transport || '',

      gst_vehicle_type: so.custom_gst_vehicle_type || '',

      custom_remark: so.custom_remark || ''
    };

    let updated = [];

    // Compare every field and update only changed values
    for (const [field, value] of Object.entries(values)) {

      if (!frm.fields_dict[field]) continue;

      const current_value = frm.doc[field];

      // Compare current Delivery Note value with Sales Order value
      if (String(current_value ?? '') !== String(value ?? '')) {

        await frm.set_value(field, value);

        updated.push(field);
      }
    }

    if (updated.length) {

      frappe.show_alert({
        message:
          'Transporter Information updated from Sales Order: ' +
          so_name,
        indicator: 'green'
      });

      console.log(
        'Updated Transporter Fields:',
        updated
      );

    } else {

      console.log(
        'Transporter Information already matched:',
        so_name
      );
    }

  } catch (error) {

    console.error(
      'Transporter Sync Error:',
      error
    );

    frappe.show_alert({
      message: 'Unable to fetch Transporter Information',
      indicator: 'red'
    });

  } finally {

    frm.__transporter_sync_running = false;
  }
}
