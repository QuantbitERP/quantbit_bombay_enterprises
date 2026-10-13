const STOCK_METHOD =
    "quantbit_bombay_enterprises.quantbit_bombay_enterprises.public.python.sales_order.get_warehouse_stock_on_date";


frappe.ui.form.on("Sales Order", {
    transaction_date(frm) {
        refresh_open_row_preview(frm);
    },

    company(frm) {
        refresh_open_row_preview(frm);
    }
});


frappe.ui.form.on("Sales Order Item", {
    form_render(frm, cdt, cdn) {
        render_stock_preview(frm, cdt, cdn);
    },

    item_code(frm, cdt, cdn) {
        const grid_row =
            frm.fields_dict.items?.grid?.grid_rows_by_docname?.[cdn];

        if (grid_row && !grid_row.grid_form) {
            grid_row.toggle_view(true);
        }

        frappe.after_ajax(() => {
            render_stock_preview(frm, cdt, cdn);
        });
    },

    qty(frm, cdt, cdn) {
        render_stock_preview(frm, cdt, cdn);
    }
});


function refresh_open_row_preview(frm) {
    const grid = frm.fields_dict.items?.grid;

    if (!grid?.grid_rows) return;

    for (const grid_row of grid.grid_rows) {
        if (
            grid_row.grid_form &&
            grid_row.grid_form.$wrapper.is(":visible")
        ) {
            render_stock_preview(
                frm,
                grid_row.doc.doctype,
                grid_row.doc.name
            );
        }
    }
}


function render_stock_preview(frm, cdt, cdn) {
    const row = locals[cdt]?.[cdn];

    if (!row) return;

    const grid = frm.fields_dict.items?.grid;
    const grid_row = grid?.grid_rows_by_docname?.[cdn];

    if (!grid_row?.grid_form) return;

    const fields = grid_row.grid_form.fields_dict;

    const section = fields.custom_section_break_jawly;

    if (section?.collapse) {
        section.collapse(false);
    }

    const html_field = fields.custom_html_preview;

    if (!html_field?.$wrapper) return;

    if (!row.item_code) {
        html_field.$wrapper.html(`
            <div class="text-muted" style="padding:8px">
                Select an Item to view stock.
            </div>
        `);
        return;
    }

    const target_date =
        frm.doc.transaction_date || frappe.datetime.get_today();

    const company = frm.doc.company;

    if (!company) {
        html_field.$wrapper.html(`
            <div class="text-muted" style="padding:8px">
                Please select a Company.
            </div>
        `);
        return;
    }

    html_field.$wrapper.html(`
        <div class="text-muted" style="padding:8px">
            <i class="fa fa-spinner fa-spin"></i>
            Loading warehouse stock...
        </div>
    `);

    frappe.call({
        method: STOCK_METHOD,

        args: {
            item_code: row.item_code,
            posting_date: target_date,
            company: company
        },

        callback(r) {
            const current_row = locals[cdt]?.[cdn];

            // Ignore stale responses if the item or form filters changed.
            if (
                !current_row ||
                current_row.item_code !== row.item_code ||
                frm.doc.company !== company ||
                (frm.doc.transaction_date || frappe.datetime.get_today())
                    !== target_date
            ) {
                return;
            }

            if (r.exc) {
                html_field.$wrapper.html(`
                    <div class="text-danger" style="padding:8px">
                        Unable to load stock. Check the server error log.
                    </div>
                `);
                return;
            }

            const data = r.message || [];

            if (!data.length) {
                html_field.$wrapper.html(`
                    <div class="text-muted" style="padding:8px">
                        No positive warehouse balance found for
                        <strong>
                            ${frappe.utils.escape_html(current_row.item_code)}
                        </strong>
                        on ${frappe.utils.escape_html(target_date)}.
                    </div>
                `);
                return;
            }

            // Current Sales Order Item quantity
            const required_qty = flt(current_row.qty);

            let rows_html = "";

            data.forEach(item => {
                const available_qty = flt(item.available_qty);

                // Yellow: stock is less than required quantity.
                // Green: stock meets or exceeds required quantity.
                const row_style = available_qty < required_qty
                    ? "background-color:#fff3cd;color:#856404;"
                    : "background-color:#d4edda;color:#155724;";

                rows_html += `
                    <tr style="${row_style}">
                        <td style="
                            padding:8px 10px;
                            border-bottom:1px solid var(--border-color);
                        ">
                            ${frappe.utils.escape_html(item.warehouse)}
                        </td>

                        <td style="
                            padding:8px 10px;
                            text-align:right;
                            border-bottom:1px solid var(--border-color);
                            font-weight:600;
                        ">
                            ${format_number(available_qty, null, 2)}
                        </td>
                    </tr>
                `;
            });

            html_field.$wrapper.html(`
                <div style="
                    border:1px solid var(--border-color);
                    border-radius:6px;
                    overflow:hidden;
                    margin:8px 0;
                ">
                    <table class="table table-sm" style="
                        width:100%;
                        margin:0;
                        font-size:12px;
                    ">
                        <thead>
                            <tr>
                                <th style="padding:8px 10px">
                                    Warehouse
                                </th>

                                <th style="
                                    padding:8px 10px;
                                    text-align:right;
                                ">
                                    Available Qty
                                </th>
                            </tr>
                        </thead>

                        <tbody>
                            ${rows_html}
                        </tbody>
                    </table>
                </div>
            `);
        }
    });
}

