
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
            Loading stock for ${frappe.utils.escape_html(target_date)}...
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
                        No positive stock inward entry found for
                        <strong>${frappe.utils.escape_html(row.item_code)}</strong>
                        on ${frappe.utils.escape_html(target_date)}.
                    </div>
                `);
                return;
            }

            let rows_html = "";

            // Quantity required in the Sales Order Item row
            const required_qty = flt(row.qty);

            data.forEach(item => {
                const stock_added = flt(item.stock_added);
                const projected_qty = flt(item.projected_qty);

                // Green when Projected Qty > required Quantity
                // Red otherwise
                const quantity_style =
                    projected_qty > required_qty
                        ? "color:#155724;background:#d4edda;"
                        : "color:#842029;background:#f8d7da;";

                rows_html += `
                    <tr>
                        <td style="
                            padding:8px 10px;
                            border-bottom:1px solid var(--border-color);
                        ">
                            <strong>
                                ${frappe.utils.escape_html(item.warehouse)}
                            </strong>
                        </td>

                        <td style="
                            padding:8px 10px;
                            text-align:right;
                            border-bottom:1px solid var(--border-color);
                        ">
                            ${format_number(stock_added, null, 2)}
                        </td>

                        <td style="
                            padding:8px 10px;
                            text-align:right;
                            border-bottom:1px solid var(--border-color);
                        ">
                            ${format_number(projected_qty, null, 2)}
                        </td>

                        <td style="
                            padding:8px 10px;
                            text-align:right;
                            border-bottom:1px solid var(--border-color);
                        ">
                            <span style="
                                display:inline-block;
                                padding:4px 8px;
                                border-radius:4px;
                                font-weight:600;
                                ${quantity_style}
                            ">
                                ${format_number(required_qty, null, 2)}
                            </span>
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
                    <div style="
                        padding:10px 12px;
                        background:var(--bg-light-gray, #f8f9fa);
                        border-bottom:1px solid var(--border-color);
                        font-size:12px;
                    ">
                        <div>
                            Stock Inward Date:
                            <strong>
                                ${frappe.utils.escape_html(target_date)}
                            </strong>
                        </div>

                        <div>
                            Company:
                            <strong>
                                ${frappe.utils.escape_html(company)}
                            </strong>
                        </div>

                        <div>
                            Item:
                            <strong>
                                ${frappe.utils.escape_html(row.item_code)}
                            </strong>
                        </div>
                    </div>

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
                                    Stock Added on Date
                                </th>

                                <th style="
                                    padding:8px 10px;
                                    text-align:right;
                                ">
                                    Projected Qty
                                </th>

                                <th style="
                                    padding:8px 10px;
                                    text-align:right;
                                ">
                                    Quantity
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