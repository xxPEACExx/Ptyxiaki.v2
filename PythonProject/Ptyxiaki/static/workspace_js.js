
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
// STATISTICS TAB
// =====================================================

let statsChart = null;

const runStatsBtn = document.getElementById("run-stats");
const statTypeSelect = document.getElementById("stat-type");
const canvas = document.getElementById("stats-chart");
const placeholder = document.getElementById("stats-placeholder");

runStatsBtn.addEventListener("click", () => {
    const type = statTypeSelect.value;

    placeholder.style.display = "none";
    canvas.style.display = "block";

    if (statsChart) {
        statsChart.destroy();
        statsChart = null;
    }
    if (type === "heatmap") {
    runGroupedBar();
}
else if (type === "kind-country") {
    runKindByCountry();
}
else if (type === "claims-abstract") {
    runClaimsVsAbstract();
}

});


function runGroupedBar() {

    fetch("/api/stats/heatmap")
        .then(r => r.json())
        .then(data => {

            if (!data.length) {
                placeholder.innerText = "No data available.";
                placeholder.style.display = "block";
                canvas.style.display = "none";
                return;
            }

            placeholder.style.display = "none";
            canvas.style.display = "block";

            const countries = [...new Set(data.map(d => d.country))];
            const kinds = [...new Set(data.map(d => d.kind))];

            // matrix[country][kind] = total
            const matrix = {};
            countries.forEach(c => {
                matrix[c] = {};
                kinds.forEach(k => matrix[c][k] = 0);
            });

            data.forEach(d => {
                matrix[d.country][d.kind] = d.total;
            });

            const datasets = kinds.map((kind, i) => ({
                label: kind,
                data: countries.map(c => matrix[c][kind]),
                backgroundColor: `rgba(47,128,237,${0.25 + i * 0.08})`,
                borderRadius: 6
            }));

            if (statsChart) statsChart.destroy();

            statsChart = new Chart(canvas.getContext("2d"), {
                type: "bar",
                data: {
                    labels: countries,
                    datasets: datasets
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: "top"
                        },
                        tooltip: {
                            callbacks: {
                                label(ctx) {
                                    return `${ctx.dataset.label}: ${ctx.parsed.y}`;
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            grid: { display: false }
                        },
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        });
}

function runKindByCountry() {

    fetch("/api/stats/kind-by-country")
        .then(r => r.json())
        .then(data => {

            if (!data.length) {
                placeholder.innerText = "No data available.";
                placeholder.style.display = "block";
                canvas.style.display = "none";
                return;
            }

            const countries = [...new Set(data.map(d => d.country))];
            const kinds = [...new Set(data.map(d => d.kind))];

            const datasets = kinds.map((kind, idx) => ({
                label: kind,
                data: countries.map(c =>
                    data.find(d => d.country === c && d.kind === kind)?.total || 0
                ),
                backgroundColor: `hsl(${idx * 60}, 70%, 55%)`
            }));

            statsChart = new Chart(canvas.getContext("2d"), {
                type: "bar",
                data: {
                    labels: countries,
                    datasets
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: "bottom"
                        },
                        tooltip: {
                            mode: "index",
                            intersect: false
                        }
                    },
                    scales: {
                        x: {
                            stacked: true,
                            grid: { display: false }
                        },
                        y: {
                            stacked: true,
                            title: {
                                display: true,
                                text: "Documents"
                            }
                        }
                    }
                }
            });

        })
        .catch(err => {
            console.error(err);
            placeholder.innerText = "Error loading statistics.";
            placeholder.style.display = "block";
            canvas.style.display = "none";
        });
}

function runClaimsVsAbstract() {
    fetch("/api/stats/claims-vs-abstract")
        .then(r => r.json())
        .then(data => {

            const points = data.points || [];

            statsChart = new Chart(canvas, {
                type: "scatter",
                data: {
                    datasets: [{
                        label: "Documents",
                        data: points,
                        backgroundColor: "rgba(47, 128, 237, 0.6)"
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
                        x: {
                            title: {
                                display: true,
                                text: "Abstract word count"
                            }
                        },
                        y: {
                            title: {
                                display: true,
                                text: "Number of claims"
                            }
                        }
                    }
                }
            });
        })
        .catch(err => {
            console.error(err);
            placeholder.innerText = "Failed to load statistic.";
            placeholder.style.display = "block";
            canvas.style.display = "none";
        });
}
document.addEventListener("DOMContentLoaded", () => {
    const sidebar = document.getElementById("sidebar");
    const content = document.getElementById("content");
    const leftZone = document.getElementById("left-zone");

    if (!sidebar || !content || !leftZone) return;

    // αρχική κατάσταση: ανοιχτό
    let isOpen = true;

    // κλείσε μετά από λίγο
    setTimeout(() => {
        sidebar.classList.add("hidden");
        content.classList.add("expanded");
        isOpen = false;
    }, 3000);

    // άνοιγμα όταν μπαίνει στο left-zone
    leftZone.addEventListener("mouseenter", () => {
        if (isOpen) return;
        sidebar.classList.remove("hidden");
        content.classList.remove("expanded");
        isOpen = true;
    });

    // κλείσιμο όταν φεύγει από το sidebar
    sidebar.addEventListener("mouseleave", () => {
        if (!isOpen) return;
        sidebar.classList.add("hidden");
        content.classList.add("expanded");
        isOpen = false;
    });
});

// ===============================
// LIVE UPDATE SUMMARY (delegation)
// ===============================
document.addEventListener("change", (e) => {
    if (e.target.closest("#tab-query") && e.target.matches("input, select")) {
        updateQuerySummary();
    }
});
