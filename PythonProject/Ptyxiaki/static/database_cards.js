
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
  const elLast = document.getElementById("stat-last-update");
  const elFpm  = document.getElementById("stat-files-per-minute");

  if (!elDocs || !elLast) return;

  elDocs.textContent = data.documents ?? "0";

  lastSummaryTs = Number(data.timestamp || 0);
  elLast.textContent = lastSummaryTs
    ? new Date(lastSummaryTs * 1000).toLocaleString("el-GR")
    : "–";

  if (elFpm) {
    elFpm.textContent =
      data.files_per_minute != null
        ? data.files_per_minute
        : "–";
  }

  const elInserted = document.getElementById("stat-last-inserted");
  if (elInserted) {
    elInserted.textContent =
      data.last_inserted != null ? data.last_inserted : "–";
  }

  const elDuration = document.getElementById("stat-duration");
  if (elDuration) {
    elDuration.textContent =
      data.last_duration != null ? `${data.last_duration}s` : "–";
  }
}


/* ===========================
   HUMAN TIME BUCKETS
   =========================== */
function formatTimeBucket(seconds) {
  if (seconds < 60) return "A Few Seconds Ago";
  if (seconds < 300) return "1 Minute Ago";
  if (seconds < 600) return "5 Minute Ago";
  if (seconds < 3600) return "10 Minute Ago";
  if (seconds < 86400) return "1 Hour Ago";
  return "More than 1 day";
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

