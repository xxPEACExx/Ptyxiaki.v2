
let currentPage = 1;
let pageSize = 1000;          // default
let totalPages = 1;
let totalRows = 0;
let lastQueryCriteria = null;



// ID → Name maps (for summary)
const kindMap = {};
const stateMap = {};

// =====================================================
// TAB SWITCHING + PERSIST ACTIVE TAB
// =====================================================
function activateTab(tabId) {
  document.querySelectorAll(".tab-button").forEach(b => b.classList.remove("active"));
  document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));

  const btn = document.querySelector(`.tab-button[data-tab="${tabId}"]`);
  const tab = document.getElementById(tabId);

  if (btn) btn.classList.add("active");
  if (tab) tab.classList.add("active");

  try { localStorage.setItem("active_tab", tabId); } catch (e) {}
}

document.querySelectorAll(".tab-button").forEach(btn => {
  btn.addEventListener("click", () => activateTab(btn.dataset.tab));
});

(function restoreTab() {
  try {
    const saved = localStorage.getItem("active_tab");
    if (saved && document.getElementById(saved)) activateTab(saved);
  } catch (e) {}
})();

// =====================================================
// HELPERS
// =====================================================
function getCheckedValues(name) {
  return Array.from(document.querySelectorAll(`input[name="${name}"]:checked`))
    .map(cb => cb.value);
}

function escapeHtml(str) {
  return String(str ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

// =====================================================
// SCROLLBAR SYNC
// =====================================================
function syncScrollForWrapper(wrapperEl) {
  if (!wrapperEl) return;

  const top = wrapperEl.querySelector(".table-scroll-top");
  const inner = wrapperEl.querySelector(".table-scroll-inner");
  const body = wrapperEl.querySelector(".table-scroll-body");
  if (!top || !inner || !body) return;

  const table = body.querySelector("table");
  if (!table) {
    inner.style.width = "1px";
    return;
  }

  inner.style.width = table.scrollWidth + "px";
  top.onscroll = () => body.scrollLeft = top.scrollLeft;
  body.onscroll = () => top.scrollLeft = body.scrollLeft;
}

function syncAllTables() {
  document.querySelectorAll(".results-table-wrapper, .table-results-wrapper")
    .forEach(syncScrollForWrapper);
}

window.addEventListener("resize", syncAllTables);

// =====================================================
// QUERY SUMMARY
// =====================================================
const summaryBox = document.getElementById("query-summary");

function updateQuerySummary() {
  if (!summaryBox) return;

  const lines = [];
  const yearFrom = document.querySelector('input[name="year_from"]')?.value || "";
  const yearTo = document.querySelector('input[name="year_to"]')?.value || "";

  const states = getCheckedValues("state").map(id => stateMap[id]).filter(Boolean);
  const kinds = getCheckedValues("kind").map(id => kindMap[id]).filter(Boolean);

  const minClaims = document.querySelector('input[name="min_claims"]')?.value || "";
  const minAbstract = document.querySelector('input[name="min_abstract_words"]')?.value || "";

  lines.push("<strong>Criteria</strong>");

  if (yearFrom || yearTo) lines.push(`Year: ${yearFrom || "…"} – ${yearTo || "…"}`);
  if (states.length) lines.push("Country: " + states.join(", "));
  if (kinds.length) lines.push("Kind: " + kinds.join(", "));
  if (minClaims) lines.push("Min claims: " + minClaims);
  if (minAbstract) lines.push("Min abstract words: " + minAbstract);

  summaryBox.innerHTML = lines.length === 1 ? "No criteria selected." : lines.join("<br>");
}

// =====================================================
// PAGE SIZE SELECTOR (NEW)
// =====================================================
const pageSizeSelect = document.getElementById("pageSizeSelect");
if (pageSizeSelect) {
  pageSizeSelect.value = String(pageSize);

  pageSizeSelect.addEventListener("change", () => {
    pageSize = Math.min(parseInt(pageSizeSelect.value, 10) || 1000, 10000);
    currentPage = 1;
    if (lastQueryCriteria) runSearch();
  });
}

// =====================================================
// RUN SEARCH
// =====================================================
const runQueryBtn = document.getElementById("run-query-btn");

if (runQueryBtn) {
  runQueryBtn.addEventListener("click", () => {
    lastQueryCriteria = {
      year_from: document.querySelector('input[name="year_from"]')?.value || null,
      year_to: document.querySelector('input[name="year_to"]')?.value || null,
      state: getCheckedValues("state"),
      kind: getCheckedValues("kind"),
      min_claims: document.querySelector('input[name="min_claims"]')?.value || null,
      min_abstract_words: document.querySelector('input[name="min_abstract_words"]')?.value || null
    };

    currentPage = 1;
    runSearch();
  });
}

function runSearch() {
  fetch("/api/search", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      criteria: lastQueryCriteria,
      page: currentPage,
      page_size: pageSize
    })
  })
    .then(r => r.json())
    .then(data => {
    activateTab("tab-query");
      totalPages = data.total_pages || 1;
      totalRows = data.total_rows || 0;
      renderQueryResults(data);
      renderPagination(currentPage, totalPages);
      updateResultsInfo();
      syncAllTables();
    })
    .catch(console.error);
}

// =====================================================
// RENDER RESULTS
// =====================================================
function renderQueryResults(data) {
console.log("results-table-query elements:", document.querySelectorAll("#results-table-query").length);

  const rt = document.getElementById("results-table-query");
  if (!rt) return;

  if (!data?.columns?.length) {
    rt.innerHTML = "No results.";
    return;
  }

  let html = '<table class="filter-results"><thead><tr><th>#</th>';
  data.columns.forEach(c => html += `<th>${escapeHtml(c)}</th>`);
  html += "</tr></thead><tbody>";

  data.rows.forEach((row, i) => {
    const idx = (currentPage - 1) * pageSize + i + 1;
    html += `<tr><td>${idx}</td>`;
    row.forEach(cell => html += `<td>${escapeHtml(cell)}</td>`);
    html += "</tr>";
  });

  html += "</tbody></table>";
  rt.innerHTML = html;
}

// =====================================================
// PAGINATION
// =====================================================
function renderPagination(page, total) {
  const container = document.getElementById("pagination");
  if (!container || total <= 1) {
    if (container) container.innerHTML = "";
    return;
  }




  container.innerHTML = "";

  if (page > 1) {
    container.innerHTML += `<button data-page="${page - 1}">« Prev</button>`;
  }

  const start = Math.max(1, page - 2);
  const end = Math.min(total, start + 4);

  for (let p = start; p <= end; p++) {
    container.innerHTML += `
      <button data-page="${p}" class="${p === page ? "active" : ""}">
        ${p}
      </button>`;
  }

  if (page < total) {
    container.innerHTML += `<button data-page="${page + 1}">Next »</button>`;
  }

  container.querySelectorAll("button").forEach(btn => {
    btn.addEventListener("click", () => {
      currentPage = Number(btn.dataset.page);
      runSearch();
    });
  });
}

// =====================================================
// LOAD FILTER DATA
// =====================================================
function loadKinds() {
  fetch("/api/kinds").then(r => r.json()).then(rows => {
    const box = document.getElementById("kind-checkboxes");
    if (!box) return;
    box.innerHTML = "";
    rows.forEach(([id, name]) => {
      kindMap[id] = name;
      box.insertAdjacentHTML("beforeend",
        `<label><input type="checkbox" name="kind" value="${id}">${name}</label>`);
    });
    updateQuerySummary();
  });
}

function loadStates() {
  fetch("/api/states").then(r => r.json()).then(rows => {
    const box = document.getElementById("state-checkboxes");
    if (!box) return;
    box.innerHTML = "";
    rows.forEach(([id, name]) => {
      stateMap[id] = name;
      box.insertAdjacentHTML("beforeend",
        `<label><input type="checkbox" name="state" value="${id}">${name}</label>`);
    });
    updateQuerySummary();
  });
}

// =====================================================
// INIT
// =====================================================
loadKinds();
loadStates();
updateQuerySummary();
syncAllTables();


// =====================================================
// STATISTICS TAB (FINAL – WORKING)
// =====================================================
let statsChart = null;

const runStatsBtn = document.getElementById("run-stats");
const statTypeSelect = document.getElementById("stat-type");
const canvas = document.getElementById("stats-chart");
const placeholder = document.getElementById("stats-placeholder");
const subtitle = document.getElementById("stats-subtitle");

function showPlaceholder(msg) {
  if (placeholder) {
    placeholder.innerText = msg || "No data available.";
    placeholder.style.display = "block";
  }
  if (canvas) canvas.style.display = "none";
}

function showCanvas() {
  if (placeholder) placeholder.style.display = "none";
  if (canvas) canvas.style.display = "block";
}

function destroyChart() {
  if (statsChart) {
    statsChart.destroy();
    statsChart = null;
  }
}

function setSubtitle(text) {
  if (subtitle) subtitle.innerText = text || "";
}

async function fetchJson(url) {
  const r = await fetch(url);
  const data = await r.json();
  if (!r.ok) throw new Error(data?.error || `HTTP ${r.status}`);
  return data;
}

if (runStatsBtn) {
  runStatsBtn.addEventListener("click", async () => {
    const type = statTypeSelect.value;
    destroyChart();

    try {
      if (type === "claims-abstract") {
        setSubtitle("Το συγκεκριμένο query αναδεικνύει τη σχέση μεταξύ του abstract word count, δηλαδή " +
          "τοΝ αριθμό λέξεων της περιγραφής ενός εγγράφου, και του αριθμού των claims, που " +
          "εκφράζουν το εύρος της νομικής προστασίας. Το abstract word count λειτουργεί ως " +
          "ένδειξη της έκτασης και της αναλυτικότητας της τεχνικής περιγραφής, ενώ τα claims " +
          "αποτυπώνουν την τεχνική και νομική πολυπλοκότητα της εφεύρεσης. Μέσα από τη " +
          "συσχέτιση των δύο μεγεθών, μπορούμε να αξιολογήσουμε κατά πόσο η αναλυτικότητα " +
          "της περιγραφής συνοδεύεται από αυξημένο αριθμό αξιώσεων προστασίας.");

        await runClaimsVsAbstract();

      } else if (type === "claims-intensity") {
        setSubtitle("Average claim intensity per document kind (EP only).");
        // NOTE: Η συνάρτηση runClaimsIntensity δεν υπάρχει στο απόσπασμα που μου έστειλες.
        // Αν υπάρχει στο πραγματικό αρχείο σου, άφησέ το όπως είναι εκεί.
        await runClaimsIntensity();

      } else if (type === "complexity") {
        setSubtitle("Το συγκεκριμένο query υπολογίζει έναν δείκτη «πολυπλοκότητας» (complexity score)" +
          "για κάθε έγγραφο, βασισμένο στον αριθμό των claims και στο μέγεθος του abstract. Συγκεκριμένα, " +
          "για κάθε έγγραφο με έγκυρα δεδομένα, συνδυάζει τον αριθμό claims και τον αριθμό λέξεων του " +
          "abstract χρησιμοποιώντας λογαριθμική κλίμακα, ώστε να αποτυπώνεται η αυξημένη πολυπλοκότητα " +
          "χωρίς να υπερτονίζονται ακραίες τιμές. Τα αποτελέσματα ταξινομούνται κατά φθίνουσα σειρά " +
          "πολυπλοκότητας και επιστρέφονται τα 1000 πιο σύνθετα έγγραφα. Με αυτόν τον τρόπο, το query " +
          "επιτρέπει τον εντοπισμό εγγράφων με υψηλό βαθμό τεχνικής ή νομικής πολυπλοκότητας, διευκολύνοντας " +
          "τη συγκριτική ανάλυση και την ανάδειξη των πιο απαιτητικών περιπτώσεων.");
        await runComplexityScore();

      } else if (type === "patents-month") {
        setSubtitle("Το συγκεκριμένο query υπολογίζει τον αριθμό εγγράφων ανά μήνα για μια " +
          "συγκεκριμένη χώρα. Συγκεκριμένα, εξάγει τον μήνα από την ημερομηνία (date) κάθε " +
          "εγγράφου και ομαδοποιεί τα δεδομένα ώστε να μετρήσει πόσα έγγραφα " +
          "καταχωρήθηκαν σε κάθε μήνα. Με αυτόν τον τρόπο, παρέχει μια χρονική κατανομή " +
          "των εγγράφων, επιτρέποντας την ανάλυση της εποχικότητας ή των τάσεων " +
          "καταχώρησης εγγράφων μέσα στο έτος για τη χώρα που επιλέγεται.");
        await runPatentsPerMonth();

      } else if (type === "growth-rate") {
        setSubtitle("Month-to-month growth rate in EP patent publications.");
        await runMonthlyGrowthRate();

      } else if (type === "maturity-time") {
        setSubtitle("Το συγκεκριμένο query υπολογίζει τη μέση τιμή του δείκτη «ωριμότητας» εγγράφων " +
          "ανά έτος για μια συγκεκριμένη χώρα (EP). Συγκεκριμένα, εξάγει το έτος από την ημερομηνία (date) " +
          "κάθε εγγράφου και ομαδοποιεί τα δεδομένα ώστε να υπολογίσει τόσο τον συνολικό αριθμό εγγράφων όσο " +
          "και τον μέσο δείκτη ωριμότητας για κάθε έτος. Ο δείκτης ωριμότητας προκύπτει από συνδυασμό του αριθμού " +
          "claims και του πλήθους λέξεων του abstract, με προκαθορισμένα βάρη. Με αυτόν τον τρόπο, το query " +
          "παρέχει μια χρονική απεικόνιση της εξέλιξης της ωριμότητας των εγγράφων, επιτρέποντας την ανάλυση μακροχρόνιων " +
          "τάσεων και τη σύγκριση της ποιότητας ή πληρότητας των εγγράφων στο πέρασμα του χρόνου.");
        await runMaturityOverTime();

      } else {
        showPlaceholder("Unknown analysis type.");
      }
    } catch (e) {
      console.error("Stats error:", e);
      showPlaceholder("Error loading analysis: " + (e.message || e));
    }
  });
}

// -----------------------------------------------------
// STAT 1: Claims vs Abstract (Scatter)
// -----------------------------------------------------
async function runClaimsVsAbstract() {
  const data = await fetchJson("/api/stats/claims-vs-abstract");
  const points = data.points || [];

  if (!points.length) {
    showPlaceholder("No data available for this analysis.");
    return;
  }

  showCanvas();

  statsChart = new Chart(canvas, {
    type: "scatter",
    data: {
      datasets: [{
        label: "Patents",
        data: points,
        backgroundColor: "rgba(52, 152, 219, 0.6)"
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        tooltip: {
          callbacks: {
            label: ctx =>
              `Abstract words: ${ctx.parsed.x}, Claims: ${ctx.parsed.y}`
          }
        }
      },
      scales: {
        x: { title: { display: true, text: "Abstract word count" } },
        y: { title: { display: true, text: "Number of claims" }, beginAtZero: true }
      }
    }
  });
}

// -----------------------------------------------------
// STAT 2: Complexity Score (Scatter – CORRECT)
// -----------------------------------------------------
async function runComplexityScore() {
  const data = await fetchJson("/api/stats/complexity-score");
  const rows = data.rows || [];

  if (!rows.length) {
    showPlaceholder("No data available for this analysis.");
    return;
  }

  const points = rows.map(r => ({
    x: r.abstract_words,
    y: r.claims,
    complexity: r.complexity
  }));

  showCanvas();

  statsChart = new Chart(canvas, {
    type: "scatter",
    data: {
      datasets: [{
        label: "Patent Complexity",
        data: points,
        backgroundColor: "rgba(231, 76, 60, 0.6)"
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        tooltip: {
          callbacks: {
            label: ctx =>
              `Abstract: ${ctx.parsed.x}, Claims: ${ctx.parsed.y}, Complexity: ${ctx.raw.complexity.toFixed(2)}`
          }
        }
      },
      scales: {
        x: { title: { display: true, text: "Abstract word count" } },
        y: { title: { display: true, text: "Number of claims" }, beginAtZero: true }
      }
    }
  });
}

// -----------------------------------------------------
// STAT 3: Maturity Over Time (Line)
// -----------------------------------------------------
async function runMaturityOverTime() {
  const data = await fetchJson("/api/stats/maturity-over-time");

  const years = (data.years || []).map(String);
  const values = (data.values || []).map(Number);

  if (!years.length || !values.length) {
    showPlaceholder("No data available for this analysis.");
    return;
  }

  showCanvas();

  statsChart = new Chart(canvas, {
    type: "line",
    data: {
      labels: years,
      datasets: [{
        label: "Average Maturity Score",
        data: values,
        tension: 0.3,
        borderWidth: 2,
        pointRadius: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        tooltip: {
          callbacks: {
            label: ctx =>
              `Average Maturity Score: ${ctx.parsed.y.toFixed(3)}`
          }
        }
      },
      scales: {
        x: { title: { display: true, text: "Publication Year" } },
        y: { title: { display: true, text: "Maturity Score" }, beginAtZero: true }
      }
    }
  });
}

// -----------------------------------------------------
// STAT 4: Patents per Month (Bar + Avg line)
// -----------------------------------------------------
async function runPatentsPerMonth() {
  const data = await fetchJson("/api/stats/patents-per-month");

  const labels = data.labels || [];
  const values = data.values || [];

  if (!labels.length || !values.length) {
    showPlaceholder("No data available.");
    return;
  }

  const avg = values.reduce((sum, v) => sum + v, 0) / values.length;

  showCanvas();

  statsChart = new Chart(canvas.getContext("2d"), {
    data: {
      labels: labels,
      datasets: [
        {
          type: "bar",
          label: "Monthly patent publications",
          data: values,
          backgroundColor: "rgba(52, 152, 219, 0.65)",
          borderRadius: 6
        },
        {
          type: "line",
          label: `Average (Patents / 12 = ${avg.toFixed(2)})`,
          data: labels.map(() => avg),
          borderColor: "rgba(231, 76, 60, 0.9)",
          borderDash: [6, 6],
          borderWidth: 3,
          hoverBorderWidth: 4,
          pointRadius: 0
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: "index",
        intersect: false
      },
      plugins: {
        legend: { position: "top" },
        tooltip: {
          mode: "index",
          intersect: false,
          callbacks: {
            label: function (ctx) {
              if (ctx.dataset.label.startsWith("Average")) {
                return `Average patents per month: ${avg.toFixed(2)}`;
              }
              return `Patents: ${ctx.parsed.y}`;
            }
          }
        }
      },
      scales: {
        x: { title: { display: true, text: "Year – Month" } },
        y: { title: { display: true, text: "Number of patents" }, beginAtZero: true }
      }
    }
  });
}

// ===============================
// LIVE UPDATE SUMMARY (delegation)
// ===============================
document.addEventListener("change", (e) => {
  if (e.target.closest("#tab-query") && e.target.matches("input, select")) {
    updateQuerySummary();
  }
});

document.addEventListener("DOMContentLoaded", () => {
  const toggleBtn = document.getElementById("themeToggle");
  const body = document.body;

  const savedTheme = localStorage.getItem("theme");
  if (savedTheme === "dark") {
    body.classList.add("dark-theme");
    toggleBtn.textContent = "🔆";
  }

  toggleBtn.addEventListener("click", () => {
    const isDark = body.classList.toggle("dark-theme");
    toggleBtn.textContent = isDark ? "🔆" : "🌓";
    localStorage.setItem("theme", isDark ? "dark" : "light");
  });
});

function updateResultsInfo() {
  const box = document.getElementById("results-info");
  if (!box) return;

  if (!totalRows || totalRows === 0) {
    box.innerHTML = "";
    return;
  }

  const from = (currentPage - 1) * pageSize + 1;
  const to = Math.min(currentPage * pageSize, totalRows);

  box.innerHTML = `
    <strong>${from.toLocaleString()}–${to.toLocaleString()}</strong>
    από
    <strong>${totalRows.toLocaleString()}</strong>
    αποτελέσματα
  `;
}

function runQueryAJAX(form) {
  const textarea = form.querySelector("textarea[name='sql_input']");
  const msgBox = document.getElementById("table-messages");

  const fd = new FormData();
  fd.append("sql_input", textarea.value);

  msgBox.textContent = "Running query…";

  fetch("/workspace_ajax", {
    method: "POST",
    body: fd
  })
    .then(r => r.json())
    .then(data => {
      if (data.error) {
        msgBox.textContent = "Error: " + data.error;
        window.setSqlResults([], []);
        return;
      }

      msgBox.innerHTML =
        `Rows: ${data.row_count} | Time: ${data.elapsed.toFixed(3)}s`;

      // 🔑 ΠΕΡΝΑΜΕ ΤΑ ΔΕΔΟΜΕΝΑ ΣΤΟ sql_direct.js
      if (typeof window.setSqlResults === "function") {
        window.setSqlResults(data.columns || [], data.rows || []);


      } else {
        console.error("setSqlResults() not found. Is sql_direct.js loaded?");
      }
    })
    .catch(err => {
      msgBox.textContent = "Request failed.";
      console.error(err);
      window.setSqlResults([], []);
    });

  return false; // ⬅️ ΑΠΑΡΑΙΤΗΤΟ για να μην γίνει submit
}


function renderSqlPage() {
  const resultsBox = document.getElementById("results-table");
  const infoBox = document.getElementById("sql-results-info");
  const total = sqlAllRows.length;

  if (!total) {
    resultsBox.innerHTML = "No results.";
    return;
  }

  const from = (sqlPage - 1) * sqlPageSize;
  const to = Math.min(from + sqlPageSize, total);

  let html = "<table class='sql-results'><thead><tr>";
  sqlColumns.forEach(c => html += `<th>${c}</th>`);
  html += "</tr></thead><tbody>";

  sqlAllRows.slice(from, to).forEach(row => {
    html += "<tr>";
    row.forEach(cell => html += `<td>${cell ?? ""}</td>`);
    html += "</tr>";
  });

  html += "</tbody></table>";
  resultsBox.innerHTML = html;

  infoBox.innerHTML = `
    <strong>${from + 1}–${to}</strong> από
    <strong>${total}</strong> αποτελέσματα
  `;

  renderSqlPagination(total);
}

function renderSqlPagination(total) {
  const box = document.getElementById("sql-pagination");
  const pages = Math.ceil(total / sqlPageSize);

  box.innerHTML = "";
  if (pages <= 1) return;

  if (sqlPage > 1) {
    box.innerHTML += `<button data-p="${sqlPage - 1}">« Prev</button>`;
  }

  for (let p = 1; p <= pages; p++) {
    box.innerHTML += `
      <button data-p="${p}" ${p === sqlPage ? 'class="active"' : ""}>
        ${p}
      </button>`;
  }

  if (sqlPage < pages) {
    box.innerHTML += `<button data-p="${sqlPage + 1}">Next »</button>`;
  }

  box.querySelectorAll("button").forEach(b => {
    b.onclick = () => {
      sqlPage = Number(b.dataset.p);
      renderSqlPage();
    };
  });
}

document.getElementById("sqlPageSize").addEventListener("change", e => {
  sqlPageSize = Number(e.target.value);
  sqlPage = 1;
  renderSqlPage();
});


function openModal({ title, placeholder, value = "", message, onConfirm }) {
  const modal = document.getElementById("sql-modal");
  const titleEl = document.getElementById("modal-title");
  const input = document.getElementById("modal-input");
  const msg = document.getElementById("modal-message");
  const ok = document.getElementById("modal-ok");
  const cancel = document.getElementById("modal-cancel");

  titleEl.textContent = title;

  if (message) {
    msg.textContent = message;
    msg.style.display = "block";
    input.style.display = "none";
  } else {
    input.placeholder = placeholder || "";
    input.value = value;
    input.style.display = "block";
    msg.style.display = "none";
  }

  modal.classList.remove("hidden");

  cancel.onclick = () => modal.classList.add("hidden");

  ok.onclick = () => {
    modal.classList.add("hidden");
    onConfirm(message ? true : input.value.trim());
  };
}


document.addEventListener("DOMContentLoaded", () => {
  const savedSelect = document.getElementById("saved-sql-select");
  const loadBtn = document.getElementById("load-sql-btn");
  const deleteBtn = document.getElementById("delete-sql-btn");
  const renameBtn = document.getElementById("rename-sql-btn");
  const saveSqlBtn = document.getElementById("save-sql-btn");

  const sqlTextarea = document.querySelector('#tab-table textarea[name="sql_input"]');
  const msgBox = document.getElementById("table-messages");

  // Guard
  if (!savedSelect || !loadBtn || !deleteBtn || !renameBtn || !saveSqlBtn || !sqlTextarea) {
    console.error("SavedQueries: missing DOM elements", {
      savedSelect, loadBtn, deleteBtn, renameBtn, saveSqlBtn, sqlTextarea
    });
    return;
  }

  let savedQueries = [];

  function getSelectedId() {
    const id = parseInt(savedSelect.value, 10);
    return Number.isFinite(id) ? id : null;
  }

  // ================= AUTO-LOAD ON SELECT =================
  savedSelect.addEventListener("change", () => {
    const id = getSelectedId();
    if (!id) return;

    const q = savedQueries.find(x => Number(x.id) === id);
    if (!q) return;

    sqlTextarea.value = q.sql_text ?? "";
    msgBox.textContent = `Loaded: ${q.name}`;
  });

  function addOptionToTop(q) {
    const opt = document.createElement("option");
    opt.value = String(q.id);
    opt.textContent = q.name;
    savedSelect.prepend(opt);
  }

  function updateOptionText(id, newName) {
    const opt = savedSelect.querySelector(`option[value="${id}"]`);
    if (opt) opt.textContent = newName;
  }

  function removeOption(id) {
    savedSelect.querySelector(`option[value="${id}"]`)?.remove();
    if (savedSelect.value === String(id)) savedSelect.value = "";
  }

  async function loadSavedQueries() {
    const res = await fetch("/api/sql/list");
    const data = await res.json();
    savedQueries = Array.isArray(data) ? data : [];

    savedSelect.innerHTML =
      `<option value="">— Saved Queries —</option>` +
      savedQueries.map(q => `<option value="${q.id}">${q.name}</option>`).join("");
  }

  loadSavedQueries().catch(err => console.error("loadSavedQueries failed", err));

  // ================= LOAD =================
  loadBtn.addEventListener("click", () => {
    const id = getSelectedId();
    if (!id) return;

    const q = savedQueries.find(x => Number(x.id) === id);
    if (!q) return;

    sqlTextarea.value = q.sql_text ?? "";
    msgBox.textContent = `Loaded: ${q.name}`;
  });

  // ================= SAVE (LIVE ADD) =================
  saveSqlBtn.addEventListener("click", () => {
    const sqlText = sqlTextarea.value.trim();
    if (!sqlText) {
      msgBox.textContent = "Nothing to save.";
      return;
    }

    openModal({
      title: "Save SQL Query",
      placeholder: "Query name",
      confirmText: "Save",
      onConfirm: async (name) => {
        if (!name) return;

        msgBox.textContent = "Saving query…";

        try {
          const res = await fetch("/api/sql/save", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name, sql_text: sqlText })
          });

          const data = await res.json();
          if (!res.ok) throw new Error(data?.error || "Save failed");

          const newQuery = { id: data.id, name, sql_text: sqlText };
          savedQueries.unshift(newQuery);
          addOptionToTop(newQuery);
          savedSelect.value = String(newQuery.id);

          msgBox.textContent = "✔ Query saved successfully.";
        } catch (e) {
          console.error(e);
          msgBox.textContent = "❌ Failed to save query.";
        }
      }
    });
  });

  // ================= DELETE (LIVE REMOVE) =================
  deleteBtn.addEventListener("click", () => {
    const id = getSelectedId();
    if (!id) return;

    openModal({
      title: "Delete SQL Query",
      message: "Are you sure you want to delete this query?",
      confirmText: "Delete",
      danger: true,
      onConfirm: async () => {
        const r = await fetch(`/api/sql/delete/${id}`, { method: "DELETE" });

        if (!r.ok) {
          msgBox.textContent = "Delete failed.";
          return;
        }

        savedQueries = savedQueries.filter(q => Number(q.id) !== id);
        removeOption(id);

        msgBox.textContent = "Query deleted.";
      }
    });
  });

  // ================= RENAME (LIVE UPDATE) =================
  renameBtn.addEventListener("click", () => {
    const id = getSelectedId();
    if (!id) return;

    const q = savedQueries.find(x => Number(x.id) === id);
    const currentName = q?.name || "";

    openModal({
      title: "Rename SQL Query",
      placeholder: "New name",
      value: currentName,
      confirmText: "Rename",
      onConfirm: async (newName) => {
        if (!newName || newName === currentName) return;

        const r = await fetch(`/api/sql/rename/${id}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name: newName })
        });

        if (!r.ok) {
          msgBox.textContent = "Rename failed.";
          return;
        }

        if (q) q.name = newName;
        updateOptionText(id, newName);

        msgBox.textContent = "Query renamed.";
      }
    });
  });
});
