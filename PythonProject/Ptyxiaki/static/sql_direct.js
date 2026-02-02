

let sqlAllRows = [];
let sqlColumns = [];
let sqlPage = 1;
let sqlPageSize = 100;


window.setSqlResults = function (columns, rows) {
  sqlColumns = columns;
  sqlAllRows = rows;
  sqlPage = 1;
  renderSqlPage();
};


function sqlEscapeHtml(str) {
  return String(str ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function renderSqlPage() {
  const resultsBox = document.getElementById("results-table");
  const infoBox = document.getElementById("sql-results-info");
  const paginationBox = document.getElementById("sql-pagination");

  if (!resultsBox || !infoBox || !paginationBox) return;

  const total = sqlAllRows.length;

  if (!total || !sqlColumns.length) {
    resultsBox.innerHTML = "No results.";
    infoBox.innerHTML = "";
    paginationBox.innerHTML = "";
    return;
  }

  let from, to;

  if (sqlPageSize === "all") {
    from = 0;
    to = total;
  } else {
    from = (sqlPage - 1) * sqlPageSize;
    to = Math.min(from + sqlPageSize, total);
  }

  let html = "<table class='sql-results'><thead><tr>";
  sqlColumns.forEach(c => html += `<th>${sqlEscapeHtml(c)}</th>`);
  html += "</tr></thead><tbody>";

  sqlAllRows.slice(from, to).forEach(row => {
    html += "<tr>";
    row.forEach(cell => html += `<td>${sqlEscapeHtml(cell)}</td>`);
    html += "</tr>";
  });

  html += "</tbody></table>";
  resultsBox.innerHTML = html;

  if (sqlPageSize === "all") {
    infoBox.innerHTML = `
      <strong>1–${total}</strong> από
      <strong>${total}</strong> αποτελέσματα
    `;
    paginationBox.innerHTML = "";
  } else {
    infoBox.innerHTML = `
      <strong>${from + 1}–${to}</strong> από
      <strong>${total}</strong> αποτελέσματα
    `;
    renderSqlPagination(total);
  }
}

function renderSqlPagination(total) {
  const box = document.getElementById("sql-pagination");
  if (!box || sqlPageSize === "all") {
    if (box) box.innerHTML = "";
    return;
  }

  const pages = Math.ceil(total / sqlPageSize);
  box.innerHTML = "";

  if (pages <= 1) return;

  if (sqlPage > 1) {
    const prev = document.createElement("button");
    prev.textContent = "« Prev";
    prev.onclick = () => {
      sqlPage--;
      renderSqlPage();
    };
    box.appendChild(prev);
  }

  for (let p = 1; p <= pages; p++) {
    const b = document.createElement("button");
    b.textContent = p;
    if (p === sqlPage) b.classList.add("active");
    b.onclick = () => {
      sqlPage = p;
      renderSqlPage();
    };
    box.appendChild(b);
  }

  if (sqlPage < pages) {
    const next = document.createElement("button");
    next.textContent = "Next »";
    next.onclick = () => {
      sqlPage++;
      renderSqlPage();
    };
    box.appendChild(next);
  }
}


document.addEventListener("DOMContentLoaded", () => {
  const sel = document.getElementById("sqlPageSize");
  if (!sel) return;

  const initVal = sel.value;
  sqlPageSize = initVal === "all" ? "all" : Number(initVal) || 100;

  sel.addEventListener("change", () => {
    const val = sel.value;
    sqlPageSize = val === "all" ? "all" : Number(val);
    sqlPage = 1;
    renderSqlPage();
  });
});

function syncSqlHorizontalScroll() {
  const body = document.getElementById("sql-scroll-body");
  const bottom = document.getElementById("sql-bottom-scroll");
  const inner = bottom?.querySelector(".sql-bottom-scroll-inner");

  if (!body || !bottom || !inner) return;

  const table = body.querySelector("table");
  if (!table) {
    inner.style.width = "1px";
    return;
  }

  // 🔑 δίνουμε πλάτος ίσο με τον πίνακα
  inner.style.width = table.scrollWidth + "px";

  // 🔁 sync κινήσεις
  bottom.onscroll = () => {
    body.scrollLeft = bottom.scrollLeft;
  };

  body.onscroll = () => {
    bottom.scrollLeft = body.scrollLeft;
  };
}

