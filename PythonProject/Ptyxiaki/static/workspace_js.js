
// =====================================================
// GLOBAL STATE (Search tab pagination)
// =====================================================
let queryOffset = 0;
const QUERY_LIMIT = 500;
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

// restore last tab (optional)
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
// TOP SCROLLBAR SYNC (works per wrapper)
// Wrapper must contain:
//   .table-scroll-top > .table-scroll-inner
//   .table-scroll-body (scroll container) containing a <table>
// =====================================================
function syncScrollForWrapper(wrapperEl) {
  if (!wrapperEl) return;

  const top = wrapperEl.querySelector(".table-scroll-top");
  const inner = wrapperEl.querySelector(".table-scroll-inner");
  const body = wrapperEl.querySelector(".table-scroll-body");

  if (!top || !inner || !body) return;

  const table = body.querySelector("table");
  if (!table) {
    // no table yet -> keep top bar but shrink
    inner.style.width = "1px";
    return;
  }

  // set "fake" width to match table width
  inner.style.width = table.scrollWidth + "px";

  // sync scroll positions
  top.onscroll = () => { body.scrollLeft = top.scrollLeft; };
  body.onscroll = () => { top.scrollLeft = body.scrollLeft; };
}

function syncAllTables() {
  document.querySelectorAll(".results-table-wrapper, .table-results-wrapper")
    .forEach(w => syncScrollForWrapper(w));
}

window.addEventListener("resize", () => syncAllTables());

// =====================================================
// QUERY SUMMARY (Search tab)
// =====================================================
const summaryBox = document.getElementById("query-summary");

function updateQuerySummary() {
  if (!summaryBox) return;

  const lines = [];

  const yearFrom = document.querySelector('input[name="year_from"]')?.value || "";
  const yearTo   = document.querySelector('input[name="year_to"]')?.value || "";

  const states = getCheckedValues("state").map(id => stateMap[id]).filter(Boolean);
  const kinds  = getCheckedValues("kind").map(id => kindMap[id]).filter(Boolean);

  const familyOnly  = document.querySelector('input[name="family_only"]')?.checked || false;
  const minClaims   = document.querySelector('input[name="min_claims"]')?.value || "";
  const minAbstract = document.querySelector('input[name="min_abstract_words"]')?.value || "";

  lines.push("<strong>Criteria</strong>");

  if (yearFrom || yearTo) lines.push(`Year: ${escapeHtml(yearFrom || "…")} – ${escapeHtml(yearTo || "…")}`);
  if (states.length) lines.push("Country / State: " + escapeHtml(states.join(", ")));
  if (kinds.length)  lines.push("Kind: " + escapeHtml(kinds.join(", ")));
  if (familyOnly)    lines.push("Unique families only");
  if (minClaims)     lines.push("Min claims: " + escapeHtml(minClaims));
  if (minAbstract)   lines.push("Min abstract words: " + escapeHtml(minAbstract));

  summaryBox.innerHTML = (lines.length === 1) ? "No criteria selected." : lines.join("<br>");
}

// =====================================================
// SEARCH TAB: RUN SEARCH
// =====================================================
const runQueryBtn = document.getElementById("run-query-btn");

if (runQueryBtn) {
  runQueryBtn.addEventListener("click", () => {
    const criteria = {
      year_from: document.querySelector('input[name="year_from"]')?.value || null,
      year_to: document.querySelector('input[name="year_to"]')?.value || null,
      state: getCheckedValues("state"),
      kind: getCheckedValues("kind"),
      family_only: document.querySelector('input[name="family_only"]')?.checked || false,
      min_claims: document.querySelector('input[name="min_claims"]')?.value || null,
      min_abstract_words: document.querySelector('input[name="min_abstract_words"]')?.value || null
    };

    queryOffset = 0;
    lastQueryCriteria = criteria;

    fetch("/api/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ criteria, limit: QUERY_LIMIT, offset: queryOffset })
    })
      .then(r => r.json())
      .then(data => {
        renderQueryResults(data);
        queryOffset += (data.rows || []).length;
        updateLoadMoreState((data.rows || []).length);

        // IMPORTANT: update scrollbar width after rendering
        syncAllTables();
      })
      .catch(err => console.error("Search error:", err));
  });
}

// =====================================================
// SEARCH TAB: RENDER RESULTS
// =====================================================
function renderQueryResults(data) {
  const rt = document.getElementById("results-table-query");
  if (!rt) return;

  if (data?.error) {
    rt.innerHTML = `<span style="color:#b00020;">Error: ${escapeHtml(data.error)}</span>`;
    return;
  }

  if (!data?.columns?.length) {
    rt.innerHTML = "No results.";
    return;
  }

  let html = "<table class='results'><thead><tr><th>#</th>";
  data.columns.forEach(col => (html += `<th>${escapeHtml(col)}</th>`));
  html += "</tr></thead><tbody>";

  (data.rows || []).forEach((row, i) => {
    html += `<tr><td>${i + 1}</td>`;
    (row || []).forEach(cell => (html += `<td>${escapeHtml(cell)}</td>`));
    html += "</tr>";
  });

  html += "</tbody></table>";
  rt.innerHTML = html;
}

// =====================================================
// SEARCH TAB: LOAD MORE
// =====================================================
const loadMoreBtn = document.getElementById("load-more-btn");

function updateLoadMoreState(count) {
  if (!loadMoreBtn) return;

  if (count < QUERY_LIMIT) {
    loadMoreBtn.disabled = true;
    loadMoreBtn.innerText = "No more results";
  } else {
    loadMoreBtn.disabled = false;
    loadMoreBtn.innerText = "Load more";
  }
}

if (loadMoreBtn) {
  loadMoreBtn.addEventListener("click", () => {
    if (!lastQueryCriteria) return;

    fetch("/api/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        criteria: lastQueryCriteria,
        limit: QUERY_LIMIT,
        offset: queryOffset
      })
    })
      .then(r => r.json())
      .then(data => {
        appendQueryResults(data);
        queryOffset += (data.rows || []).length;
        updateLoadMoreState((data.rows || []).length);

        syncAllTables();
      })
      .catch(err => console.error("Load more error:", err));
  });
}

function appendQueryResults(data) {
  const tbody = document.querySelector("#results-table-query table tbody");
  if (!tbody || !data?.rows?.length) return;

  let startIndex = tbody.children.length;

  data.rows.forEach((row, i) => {
    const tr = document.createElement("tr");
    tr.innerHTML =
      `<td>${startIndex + i + 1}</td>` +
      (row || []).map(c => `<td>${escapeHtml(c)}</td>`).join("");
    tbody.appendChild(tr);
  });
}

// =====================================================
// TABLE TAB: AJAX SQL EXECUTION (THIS FIXES YOUR RELOAD BUG)
// Called by: <form onsubmit="return runQueryAJAX(this)">
// =====================================================
function runQueryAJAX(form) {
  try {
    const formData = new FormData(form);

    fetch("/workspace_ajax", {
      method: "POST",
      body: formData
    })
      .then(r => r.json())
      .then(updateUIWithResults)
      .then(() => syncAllTables())
      .catch(err => console.error(err));

  } catch (e) {
    console.error("runQueryAJAX failed:", e);
  }

  return false; // prevent page reload (CRITICAL)
}

// expose to inline HTML handler
window.runQueryAJAX = runQueryAJAX;

// =====================================================
// TABLE TAB: UPDATE UI WITH RESULTS
// =====================================================
function updateUIWithResults(data) {
  const tm = document.getElementById("table-messages");
  const rt = document.getElementById("results-table");

  if (tm) {
    tm.innerHTML =
      (data?.error
        ? `<span style="color:#b00020;">Error: ${escapeHtml(data.error)}</span>`
        : `<span style="color:#0c7b20;">No SQL error.</span>`) +
      `<br>Row count: ${escapeHtml(data?.row_count ?? 0)}` +
      `<br>Execution time: ${Number(data?.elapsed ?? 0).toFixed(4)} sec`;
  }

  if (!rt) return;

  if (data?.error) {
    rt.innerHTML = `<span style="color:#b00020;">Error: ${escapeHtml(data.error)}</span>`;
    return;
  }

  if (!data?.columns?.length) {
    rt.innerHTML = "No results.";
    return;
  }

  let html = "<table class='results'><thead><tr><th>#</th>";
  data.columns.forEach(col => (html += `<th>${escapeHtml(col)}</th>`));
  html += "</tr></thead><tbody>";

  (data.rows || []).forEach((row, i) => {
    html += `<tr><td>${i + 1}</td>`;
    (row || []).forEach(cell => (html += `<td>${escapeHtml(cell)}</td>`));
    html += "</tr>";
  });

  html += "</tbody></table>";
  rt.innerHTML = html;
}

// =====================================================
// LOAD KINDS & STATES
// =====================================================
function loadKinds() {
  fetch("/api/kinds")
    .then(r => r.json())
    .then(rows => {
      const box = document.getElementById("kind-checkboxes");
      if (!box) return;

      box.innerHTML = "";
      rows.forEach(([id, name]) => {
        kindMap[id] = name;
        box.insertAdjacentHTML("beforeend", `
          <label>
            <input type="checkbox" name="kind" value="${escapeHtml(id)}">
            ${escapeHtml(name)}
          </label>
        `);
      });

      updateQuerySummary();
    })
    .catch(err => console.error("loadKinds error:", err));
}

function loadStates() {
  fetch("/api/states")
    .then(r => r.json())
    .then(rows => {
      const box = document.getElementById("state-checkboxes");
      if (!box) return;

      box.innerHTML = "";
      rows.forEach(([id, name]) => {
        stateMap[id] = name;
        box.insertAdjacentHTML("beforeend", `
          <label>
            <input type="checkbox" name="state" value="${escapeHtml(id)}">
            ${escapeHtml(name)}
          </label>
        `);
      });

      updateQuerySummary();
    })
    .catch(err => console.error("loadStates error:", err));
}

// =====================================================
// INIT
// =====================================================
loadKinds();
loadStates();

// update summary on any input change inside Search tab


updateQuerySummary();

// ensure scrollbars are ready even before first run
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
        setSubtitle("Το συγκεκριμένο query αναδεικνύει τη σχέση μεταξύ του abstract word count, δηλαδή"+
        "του αριθμού λέξεων της περιγραφής ενός εγγράφου, και του αριθμού των claims, που"+
        "εκφράζουν το εύρος της νομικής προστασίας. Ο abstract word count λειτουργεί ως"+
        "ένδειξη της έκτασης και της αναλυτικότητας της τεχνικής περιγραφής, ενώ τα claims"+
        "αποτυπώνουν την τεχνική και νομική πολυπλοκότητα της εφεύρεσης. Μέσα από τη"+
        "συσχέτιση των δύο μεγεθών, μπορούμε να αξιολογήσουμε κατά πόσο η αναλυτικότητα"+
        "της περιγραφής συνοδεύεται από αυξημένο αριθμό αξιώσεων προστασίας.");

        await runClaimsVsAbstract();
      } else if (type === "claims-intensity") {
        setSubtitle("Average claim intensity per document kind (EP only).");
        await runClaimsIntensity();
      } else if (type === "complexity") {
        setSubtitle("Top complex EP patents based on structural characteristics.");
        await runComplexityScore();
      } else if (type === "patents-month") {
        setSubtitle("Το συγκεκριμένο query υπολογίζει τον αριθμό εγγράφων ανά μήνα για μια"+
        "συγκεκριμένη χώρα. Συγκεκριμένα, εξάγει τον μήνα από την ημερομηνία (date) κάθε"+
        "εγγράφου και ομαδοποιεί τα δεδομένα ώστε να μετρήσει πόσα έγγραφα"+
        "καταχωρήθηκαν σε κάθε μήνα. Με αυτόν τον τρόπο, παρέχει μια χρονική κατανομή"+
        "των εγγράφων, επιτρέποντας την ανάλυση της εποχικότητας ή των τάσεων"+
        "καταχώρησης εγγράφων μέσα στο έτος για τη χώρα που επιλέγεται.");
        await runPatentsPerMonth();
      } else if (type === "growth-rate") {
        setSubtitle("Month-to-month growth rate in EP patent publications.");
        await runMonthlyGrowthRate();
//      } else if (type === "seasonality") {
//        setSubtitle("Seasonality pattern of EP publications across months of the year.");
//        await runSeasonality();
      } else if (type === "maturity-time") {
        setSubtitle("Temporal evolution of patent maturity across publication years (EP only).");
        await runMaturityOverTime(); // το έχεις ήδη, το κρατάμε
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
// Endpoint: /api/stats/claims-vs-abstract
// returns: { points: [{x, y}, ...] }
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
// Endpoint: /api/stats/complexity-score
// returns: { rows: [{abstract_words, claims, complexity}, ...] }
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
// Endpoint: /api/stats/maturity-over-time
// returns: { years:[...], values:[...] }
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
// STAT 4: Patents per Month (Line)
// Endpoint: /api/stats/patents-per-month
// Returns: { labels:[YYYY-MM], values:[count] }
// -----------------------------------------------------
async function runPatentsPerMonth() {
  const data = await fetchJson("/api/stats/patents-per-month");

  const labels = data.labels || [];
  const values = data.values || [];

  if (!labels.length || !values.length) {
    showPlaceholder("No data available.");
    return;
  }

  // Average patents per month (Patents / 12 logic already aggregated)
  const avg =
    values.reduce((sum, v) => sum + v, 0) / values.length;

  showCanvas();

  statsChart = new Chart(canvas.getContext("2d"), {
    data: {
      labels: labels,
      datasets: [
        // ============================
        // Monthly bars
        // ============================
        {
          type: "bar",
          label: "Monthly patent publications",
          data: values,
          backgroundColor: "rgba(52, 152, 219, 0.65)",
          borderRadius: 6
        },

        // ============================
        // Average reference line
        // ============================
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
        legend: {
          position: "top"
        },
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
        x: {
          title: {
            display: true,
            text: "Year – Month"
          }
        },
        y: {
          title: {
            display: true,
            text: "Number of patents"
          },
          beginAtZero: true
        }
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