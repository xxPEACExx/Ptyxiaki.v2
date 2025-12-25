
// ==========================================
// NEW SEARCH + SORTING SYSTEM (FINAL VERSION)
// ==========================================

// Select elements
const searchInput = document.querySelector(".input-group input");
const tableRows = document.querySelectorAll("tbody tr");
const tableHeadings = document.querySelectorAll("thead th");

// ----------------------
// SEARCH FUNCTION
// ----------------------
if (searchInput) {
    searchInput.addEventListener("input", () => {
        const value = searchInput.value.toLowerCase().trim();

        tableRows.forEach((row, i) => {
            const rowText = row.textContent.toLowerCase();

            const match = rowText.includes(value);

            // Add/remove hide class for animation
            row.classList.toggle("hide", !match);

            // Add row animation delay
            row.style.setProperty("--delay", i / 25 + "s");
        });

        // Re-apply zebra striping to visible rows
        document
            .querySelectorAll("tbody tr:not(.hide)")
            .forEach((visibleRow, index) => {
                visibleRow.style.backgroundColor =
                    index % 2 === 0 ? "transparent" : "#0000000b";
            });
    });
}

// ----------------------
// SORTING FUNCTIONALITY
// ----------------------
tableHeadings.forEach((heading, index) => {
    let ascending = true;

    heading.addEventListener("click", () => {
        // Reset all headers
        tableHeadings.forEach(h => h.classList.remove("active", "asc"));
        heading.classList.add("active");

        // Toggle direction
        heading.classList.toggle("asc", ascending);
        ascending = !ascending;

        sortTable(index, !ascending);
    });
});

function sortTable(columnIndex, ascending) {
    const sorted = [...tableRows].sort((a, b) => {
        const aVal = a.children[columnIndex].textContent.trim().toLowerCase();
        const bVal = b.children[columnIndex].textContent.trim().toLowerCase();

        return ascending
            ? aVal.localeCompare(bVal)
            : bVal.localeCompare(aVal);
    });

    const tbody = document.querySelector("tbody");
    sorted.forEach(row => tbody.appendChild(row));
}

// ==========================================
// EXPORT FUNCTIONS (UNCHANGED FROM TEMPLATE)
// ==========================================

const pdf_btn = document.querySelector('#toPDF');
const customers_table = document.querySelector('#customers_table');

const toPDF = function (customers_table) {
    const html_code = `
    <!DOCTYPE html>
    <link rel="stylesheet" type="text/css" href="style.css">
    <main class="table" id="customers_table">${customers_table.innerHTML}</main>`;

    const new_window = window.open();
    new_window.document.write(html_code);

    setTimeout(() => {
        new_window.print();
        new_window.close();
    }, 400);
};

if (pdf_btn) {
    pdf_btn.onclick = () => {
        toPDF(customers_table);
    };
}

const json_btn = document.querySelector('#toJSON');

const toJSON = function (table) {
    let table_data = [],
        t_head = [],

        t_headings = table.querySelectorAll('th'),
        t_rows = table.querySelectorAll('tbody tr');

    for (let t_heading of t_headings) {
        let actual_head = t_heading.textContent.trim().split(' ');
        t_head.push(actual_head.join(' ').toLowerCase());
    }

    t_rows.forEach(row => {
        const row_object = {},
            t_cells = row.querySelectorAll('td');

        t_cells.forEach((t_cell, cell_index) => {
            row_object[t_head[cell_index]] = t_cell.textContent.trim();
        });

        table_data.push(row_object);
    });

    return JSON.stringify(table_data, null, 4);
};

if (json_btn) {
    json_btn.onclick = () => {
        const json = toJSON(customers_table);
        downloadFile(json, 'json');
    };
}

const csv_btn = document.querySelector('#toCSV');

const toCSV = function (table) {
    const t_heads = table.querySelectorAll('th'),
        tbody_rows = table.querySelectorAll('tbody tr');

    const headings = [...t_heads].map(head => {
        return head.textContent.trim().toLowerCase();
    }).join(',');

    const table_data = [...tbody_rows].map(row => {
        const cells = row.querySelectorAll('td');
        return [...cells].map(cell => cell.textContent.replace(/,/g, ".").trim()).join(',');
    }).join('\n');

    return headings + '\n' + table_data;
};

if (csv_btn) {
    csv_btn.onclick = () => {
        const csv = toCSV(customers_table);
        downloadFile(csv, 'csv', 'customer_orders');
    };
}

const excel_btn = document.querySelector('#toEXCEL');

const toExcel = function (table) {
    const t_heads = table.querySelectorAll('th'),
        tbody_rows = table.querySelectorAll('tbody tr');

    const headings = [...t_heads]
        .map(head => head.textContent.trim().toLowerCase())
        .join('\t');

    const table_data = [...tbody_rows]
        .map(row => {
            const cells = row.querySelectorAll('td');
            return [...cells]
                .map(cell => cell.textContent.trim())
                .join('\t');
        })
        .join('\n');

    return headings + '\n' + table_data;
};

if (excel_btn) {
    excel_btn.onclick = () => {
        const excel = toExcel(customers_table);
        downloadFile(excel, 'excel');
    };
}

const downloadFile = function (data, fileType, fileName = '') {
    const a = document.createElement('a');
    a.download = fileName;

    const mime_types = {
        json: 'application/json',
        csv: 'text/csv',
        excel: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    };

    a.href = `data:${mime_types[fileType]};charset=utf-8,${encodeURIComponent(data)}`;
    document.body.appendChild(a);
    a.click();
    a.remove();
};

// ==========================================
// SIDEBAR + BUBBLES SYSTEM (UNCHANGED)
// ==========================================

document.addEventListener("DOMContentLoaded", () => {

    const sidebar = document.getElementById("sidebar");
    const content = document.getElementById("content");
    const leftZone = document.getElementById("left-zone");

    if (!sidebar || !content || !leftZone) {
        console.warn("Sidebar: Missing elements");
        return;
    }

    let savedState = sessionStorage.getItem("sidebarState");

    if (savedState === "hidden") {
        sidebar.classList.add("hidden");
        content.classList.add("expanded");
    }
    else if (savedState === "shown") {
        sidebar.classList.remove("hidden");
        content.classList.remove("expanded");
    }

    if (!savedState) {
        setTimeout(() => {
            hideSidebar();
        }, 8000);
    }

    leftZone.addEventListener("mouseenter", () => {
        showSidebar();
    });

    sidebar.addEventListener("mouseleave", () => {
        hideSidebar();
    });

    document.querySelectorAll(".pagination a").forEach(btn => {
        btn.addEventListener("click", () => {
            sessionStorage.setItem("paginationClick", "true");

            if (sidebar.classList.contains("hidden")) {
                sessionStorage.setItem("sidebarState", "hidden");
            } else {
                sessionStorage.setItem("sidebarState", "shown");
            }
        });
    });

    window.addEventListener("beforeunload", () => {
        if (!sessionStorage.getItem("paginationClick")) {
            sessionStorage.removeItem("sidebarState");
        }
        sessionStorage.removeItem("paginationClick");
    });

    const rows = document.querySelectorAll("tbody tr");

    rows.forEach(row => {
        const ucidCell = row.children[1];
        if (ucidCell && ucidCell.textContent.trim() !== "") {
            const value = ucidCell.textContent.trim();
            ucidCell.innerHTML = `<span class="ucid-bubble">${value}</span>`;
        }

        const dateCell = row.children[5];
        if (dateCell && dateCell.textContent.trim() !== "") {
            const value = dateCell.textContent.trim();
            dateCell.innerHTML = `<span class="date-bubble">${value}</span>`;
        }

        const sizeCell = row.children[9];
        if (sizeCell && sizeCell.textContent.trim() !== "") {
            const value = sizeCell.textContent.trim();
            sizeCell.innerHTML = `<span class="size-bubble">${value}</span>`;
        }
    });

    function showSidebar() {
        sidebar.classList.remove("hidden");
        content.classList.remove("expanded");
    }

    function hideSidebar() {
        sidebar.classList.add("hidden");
        content.classList.add("expanded");
    }
});
