
let wasBusy = false;
let summaryTimer = null;
let lastSummaryTs = null;
const SUMMARY_CACHE_KEY = "db_summary_cache_v1";
let handledDone = false;


function invalidateSummaryCache() {
  sessionStorage.removeItem(SUMMARY_CACHE_KEY);
}

async function fetchDatabaseSummary(force = false) {
  try {
    if (!force) {
      const cached = sessionStorage.getItem(SUMMARY_CACHE_KEY);
      if (cached) {
        applySummary(JSON.parse(cached));
        updateSeconds();
        return;
      }
    }

    const r = await fetch("/api/database/summary", { cache: "no-store" });
    if (!r.ok) return;

    const data = await r.json();
    sessionStorage.setItem(SUMMARY_CACHE_KEY, JSON.stringify(data));
    applySummary(data);
    updateSeconds();

  } catch (e) {
    console.error("summary error", e);
  }
}

function applySummary(data) {
  const elDocs = document.getElementById("stat-documents");
  const elFolders = document.getElementById("stat-folders");
  const elLast = document.getElementById("stat-last-update");

  if (!elDocs || !elFolders || !elLast) return;

  elDocs.textContent = data.documents ?? "0";
  elFolders.textContent = data.folders ?? "0";

  lastSummaryTs = Number(data.timestamp || 0);
  elLast.textContent = lastSummaryTs
    ? new Date(lastSummaryTs * 1000).toLocaleString("el-GR")
    : "–";
}

/* ===========================
   HUMAN TIME BUCKETS
   =========================== */
function formatTimeBucket(seconds) {
  if (seconds < 60) return "Πριν λίγα δευτερόλεπτα";
  if (seconds < 300) return "Πριν 1 λεπτό";
  if (seconds < 600) return "Πριν 5 λεπτά";
  if (seconds < 3600) return "Πριν 10 λεπτά";
  if (seconds < 86400) return "Πριν 1 ώρα";
  return "Πριν 1 μέρα";
}

function updateSeconds() {
  const el = document.getElementById("stat-seconds");
  if (!el || !lastSummaryTs) {
    if (el) el.textContent = "–";
    return;
  }

  const now = Math.floor(Date.now() / 1000);
  el.textContent = formatTimeBucket(Math.max(0, now - lastSummaryTs));
}

async function watchProcessingState() {
  try {
    const r = await fetch("/get_progress", { cache: "no-store" });
    if (!r.ok) return;

    const data = await r.json();
    const phase = (data.phase || "").toLowerCase();
    const busy = ["upload", "unzip", "processing"].includes(phase);

    // 1️⃣ ΟΣΟ ΤΡΕΧΕΙ → reset flags
    if (busy) {
      wasBusy = true;
      handledDone = false;
      return;
    }

    // 2️⃣ ΜΟΛΙΣ ΤΕΛΕΙΩΣΕ → ΕΝΗΜΕΡΩΣΗ CARDS
    if (data.finished === true && !handledDone) {
      handledDone = true;
      wasBusy = false;

      invalidateSummaryCache();
      fetchDatabaseSummary(true);

      return;
    }

  } catch (e) {
    console.error("watchProcessingState error", e);
  }
}


document.addEventListener("DOMContentLoaded", () => {
  fetchDatabaseSummary();
  updateSeconds();

  setInterval(updateSeconds, 60000);
  setInterval(watchProcessingState, 1500);

  const confirmBtn = document.getElementById("deleteConfirmBtn");
  if (confirmBtn) {
    confirmBtn.addEventListener("click", () => {
      invalidateSummaryCache();
      fetchDatabaseSummary(true);
      setTimeout(() => fetchDatabaseSummary(true), 800);
    }, true);
  }
});



async function insertNewDocumentsOnce() {
  const lastDid = getLastDidOnTable();
  const res = await fetch(`/api/documents/new?after=${lastDid}`);
  const rows = await res.json();

  if (!rows.length) return;

  const tbody = document.querySelector("tbody");

  rows.reverse().forEach(row => {
    const tr = renderRow(row);
    tbody.prepend(tr);
    requestAnimationFrame(() => tr.style.opacity = "1");
  });

  // ενημέρωση summary
  if (window.invalidateSummaryCache) invalidateSummaryCache();
  if (window.fetchDatabaseSummary) fetchDatabaseSummary(true);
}

