//
//let isPaused = false;
//let userStopped = false;
//let phasePollInterval = null;
//let pendingFile = null;
//
//
//const UploadState = {
//  phase: "idle",        // idle | upload | unzip | processing | done | stopped
//  progress: 0,
//  lastUploadPercent: 0  // client-side upload % (single source for upload phase)
//};
//
//
//function $(id) { return document.getElementById(id); }
//
//
//function showUploadPopup() {
//  $("upload-popup")?.classList.remove("hidden");
//}
//
//function hideUploadPopup() {
//  $("upload-popup")?.classList.add("hidden");
//}
//
//function updateUploadProgress(percent) {
//  const circle = $("progress-circle");
//  if (!circle) return;
//
//  // Same approach as your original (fallback to 219)
//  const max = circle.getTotalLength ? circle.getTotalLength() : 219;
//  circle.style.strokeDashoffset = max - (percent / 100) * max;
//
//  const pct = $("upload-percent");
//  if (pct) pct.innerText = Math.round(percent) + "%";
//}
//
//function renderProgress(percent, text) {
//  UploadState.progress = percent;
//  updateUploadProgress(percent);
//
//  if (text) {
//    const status = $("upload-status");
//    if (status) status.textContent = text;
//  }
//}
//
//
//function enableControls() {
//  const pauseBtn = $("pause-btn");
//  const stopBtn = $("stop-btn");
//  if (!pauseBtn || !stopBtn) return;
//
//  pauseBtn.disabled = false;
//  stopBtn.disabled = false;
//
//  // Critical: reflect current pause state
//  pauseBtn.textContent = isPaused ? "▶️ Συνέχεια" : "⏸ Παύση";
//
//  pauseBtn.onclick = async () => {
//    const action = isPaused ? "continue" : "pause";
//
//    try {
//      await fetch("/control", {
//        method: "POST",
//        headers: { "Content-Type": "application/json" },
//        body: JSON.stringify({ action })
//      });
//
//      // Toggle local state and update label (this was missing/incorrect before)
//      isPaused = !isPaused;
//      pauseBtn.textContent = isPaused ? "▶️ Συνέχεια" : "⏸ Παύση";
//    } catch (e) {
//      console.error("Pause/Continue error:", e);
//    }
//  };
//
//  stopBtn.onclick = async () => {
//    userStopped = true;
//    try {
//      await fetch("/control", {
//        method: "POST",
//        headers: { "Content-Type": "application/json" },
//        body: JSON.stringify({ action: "stop" })
//      });
//    } catch (e) {
//      console.error("Stop error:", e);
//    }
//  };
//}
//
//function disableControls() {
//  const pauseBtn = $("pause-btn");
//  const stopBtn = $("stop-btn");
//  if (pauseBtn) pauseBtn.disabled = true;
//  if (stopBtn) stopBtn.disabled = true;
//}
//
//
//function stopPhasePolling() {
//  if (phasePollInterval) {
//    clearInterval(phasePollInterval);
//    phasePollInterval = null;
//  }
//}
//
//function startPhasePolling() {
//  if (phasePollInterval) return;
//
//  phasePollInterval = setInterval(async () => {
//    try {
//      const res = await fetch("/get_progress", { cache: "no-store" });
//      const data = await res.json();
//
//      const backendPhase = data.phase || "idle";
//
//      // STOPPED / DONE have priority
//      if (backendPhase === "stopped") {
//        UploadState.phase = "stopped";
//        renderProgress(100, "Διακόπηκε.");
//        disableControls();
//        stopPhasePolling();
//        setTimeout(hideUploadPopup, 1500);
//        return;
//      }
//
//      if (backendPhase === "done") {
//        UploadState.phase = "done";
//        renderProgress(100, "Ολοκληρώθηκε!");
//        disableControls();
//        stopPhasePolling();
//        setTimeout(hideUploadPopup, 1500);
//        return;
//      }
//
//      // UPLOAD phase: do NOT trust backend % (backend does not provide upload % here)
//      if (backendPhase === "upload") {
//        UploadState.phase = "upload";
//        const p = Math.max(1, Math.min(100, UploadState.lastUploadPercent || 1));
//        renderProgress(p, "Uploading ZIP...");
//        // Controls usually disabled while uploading
//        disableControls();
//        return;
//      }
//
//      // UNZIP phase: uses backend zip_progress
//      if (backendPhase === "unzip") {
//        UploadState.phase = "unzip";
//        const zp = Number.isFinite(data.zip_progress) ? data.zip_progress : 0;
//        const p = Math.max(1, Math.min(100, zp || 1));
//        renderProgress(p, "Unzipping files...");
//        // keep controls disabled during unzip
//        disableControls();
//        return;
//      }
//
//      // PROCESSING phase: uses backend progress + paused status
//      if (backendPhase === "processing") {
//        UploadState.phase = "processing";
//
//        const paused = data.status === "paused";
//        const pr = Number.isFinite(data.progress) ? data.progress : 0;
//        const p = Math.max(1, Math.min(100, pr || 1));
//
//        // Important: If backend says paused, reflect it in UI text AND local state
//        // This ensures correct label even if user refreshes.
//        isPaused = !!paused;
//        enableControls();
//
//        renderProgress(p, paused ? "Σε παύση..." : "Processing XML...");
//        return;
//      }
//
//      // Fallback
//      UploadState.phase = backendPhase;
//
//    } catch (e) {
//      console.error("Phase poll error:", e);
//      // Keep UI as-is on transient errors
//    }
//  }, 500);
//}
//
//
//function showDuplicateModal(message) {
//  const modal = $("duplicateModal");
//  const msg = $("duplicateModalMessage");
//
//  if (msg) msg.textContent = message || "Το αρχείο έχει ήδη ανέβει.";
//  if (modal) modal.style.display = "flex";
//}
//
//function hideDuplicateModal() {
//  const modal = $("duplicateModal");
//  if (modal) modal.style.display = "none";
//}
//
//document.addEventListener("DOMContentLoaded", () => {
//  $("duplicateModalOk")?.addEventListener("click", hideDuplicateModal);
//});
//
//
//document.addEventListener("DOMContentLoaded", () => {
//  const uploadBtn = $("uploadBtn");
//  if (!uploadBtn) return;
//
//  const zipInput = document.createElement("input");
//  zipInput.type = "file";
//  zipInput.accept = ".zip";
//  zipInput.style.display = "none";
//  document.body.appendChild(zipInput);
//
//  uploadBtn.addEventListener("click", () => zipInput.click());
//
//  zipInput.addEventListener("change", async () => {
//    const file = zipInput.files[0];
//    if (!file) return;
//
//    // reset UI state
//    stopPhasePolling();
//    isPaused = false;
//    userStopped = false;
//    UploadState.phase = "upload";
//    UploadState.progress = 0;
//    UploadState.lastUploadPercent = 1;
//
//    disableControls();
//    renderProgress(1, "Preparing upload...");
//    showUploadPopup();
//
//    if (!file.name.toLowerCase().endsWith(".zip")) {
//      alert("Μόνο ZIP αρχεία.");
//      hideUploadPopup();
//      return;
//    }
//
//    // Start polling immediately so UI follows backend phase transitions
//    startPhasePolling();
//
//    const CHUNK_SIZE = 20 * 1024 * 1024; // 20MB
//    const totalChunks = Math.ceil(file.size / CHUNK_SIZE);
//    const uploadId = crypto.randomUUID();
//
//    // During upload we want 1..100
//    UploadState.lastUploadPercent = 1;
//    renderProgress(1, "Uploading ZIP...");
//
//    for (let index = 0; index < totalChunks; index++) {
//      const start = index * CHUNK_SIZE;
//      const end = Math.min(start + CHUNK_SIZE, file.size);
//      const chunk = file.slice(start, end);
//
//      const formData = new FormData();
//      formData.append("chunk", chunk);
//      formData.append("upload_id", uploadId);
//      formData.append("filename", file.name);
//      formData.append("index", index);
//      formData.append("total", totalChunks);
//
//      let res;
//      try {
//        res = await fetch("/upload_zip_chunk", { method: "POST", body: formData });
//      } catch (e) {
//        renderProgress(1, "Σφάλμα στο upload.");
//        stopPhasePolling();
//        setTimeout(hideUploadPopup, 2000);
//        return;
//      }
//
//      // HTTP-level error
//      if (!res.ok) {
//        renderProgress(1, "Σφάλμα στο upload.");
//        stopPhasePolling();
//        setTimeout(hideUploadPopup, 2000);
//        return;
//      }
//
//      // Parse JSON
//      const data = await res.json();
//
//      // Duplicate ZIP detected
//      if (data.already_exists) {
//  stopPhasePolling();
//  hideUploadPopup();
//  pendingFile = file;   // 👈 αποθηκεύουμε το αρχείο
//  showDuplicateModal(data.message || "Το αρχείο έχει ήδη ανέβει.");
//  return;
//}
//
//
//      // Update client-side % for upload phase
//      const percent = ((index + 1) / totalChunks) * 100;
//      UploadState.lastUploadPercent = Math.max(1, Math.min(100, percent));
//      renderProgress(UploadState.lastUploadPercent, "Uploading ZIP...");
//    }
//
//    // After last chunk sent: backend moves to unzip/processing.
//    // Polling will switch phase; keep UI consistent.
//    renderProgress(100, "Upload ολοκληρώθηκε. Αναμονή για unzip...");
//  });
//});
//
//
//(async function restoreProgressIfNeeded() {
//  try {
//    const res = await fetch("/get_progress", { cache: "no-store" });
//    const data = await res.json();
//
//    if (!data.phase || data.phase === "idle" || data.phase === "done") return;
//
//    showUploadPopup();
//    startPhasePolling();
//
//    // Don't force 100; poll handles phases properly
//    if (data.phase === "upload") renderProgress(1, "Uploading ZIP...");
//    if (data.phase === "unzip") renderProgress(1, "Unzipping files...");
//    if (data.phase === "processing") renderProgress(1, "Processing XML...");
//
//  } catch (e) {
//    console.error("Restore progress failed", e);
//  }
//})();
//
//document.getElementById("duplicateNo")?.addEventListener("click", () => {
//  pendingFile = null;
//  hideDuplicateModal();
//  // δεν κάνουμε τίποτα άλλο → επιστροφή στην εφαρμογή
//});
//
//document.getElementById("duplicateYes")?.addEventListener("click", async () => {
//  hideDuplicateModal();
//
//  if (!pendingFile) return;
//
//  await startUpload(pendingFile, true); // force = true
//  pendingFile = null;
//});

let isPaused = false;
let userStopped = false;
let phasePollInterval = null;
let pendingFile = null;

const UploadState = {
  phase: "idle",        // idle | upload | unzip | processing | done | stopped
  progress: 0,
  lastUploadPercent: 0
};

function $(id) {
  return document.getElementById(id);
}

/* ================= UI ================= */

function showUploadPopup() {
  $("upload-popup")?.classList.remove("hidden");
}

function hideUploadPopup() {
  $("upload-popup")?.classList.add("hidden");
}

function updateUploadProgress(percent) {
  const circle = $("progress-circle");
  if (!circle) return;

  const max = circle.getTotalLength ? circle.getTotalLength() : 219;
  circle.style.strokeDashoffset = max - (percent / 100) * max;

  const pct = $("upload-percent");
  if (pct) pct.innerText = Math.round(percent) + "%";
}

function renderProgress(percent, text) {
  UploadState.progress = percent;
  updateUploadProgress(percent);
  if (text) $("upload-status").textContent = text;
}

/* ================= CONTROLS ================= */

function enableControls() {
  const pauseBtn = $("pause-btn");
  const stopBtn = $("stop-btn");
  if (!pauseBtn || !stopBtn) return;

  pauseBtn.disabled = false;
  stopBtn.disabled = false;
  pauseBtn.textContent = isPaused ? "▶️ Συνέχεια" : "⏸ Παύση";

  pauseBtn.onclick = async () => {
    const action = isPaused ? "continue" : "pause";
    await fetch("/control", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action })
    });
    isPaused = !isPaused;
    pauseBtn.textContent = isPaused ? "▶️ Συνέχεια" : "⏸ Παύση";
  };

  stopBtn.onclick = async () => {
    userStopped = true;
    await fetch("/control", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: "stop" })
    });
  };
}

function disableControls() {
  const pauseBtn = $("pause-btn");
  const stopBtn = $("stop-btn");
  if (pauseBtn) pauseBtn.disabled = true;
  if (stopBtn) stopBtn.disabled = true;
}

/* ================= PHASE POLLING ================= */

function stopPhasePolling() {
  if (phasePollInterval) {
    clearInterval(phasePollInterval);
    phasePollInterval = null;
  }
}

function startPhasePolling() {
  if (phasePollInterval) return;

  phasePollInterval = setInterval(async () => {
    try {
      const res = await fetch("/get_progress", { cache: "no-store" });
      const data = await res.json();
      const backendPhase = data.phase || "idle";

      if (backendPhase === "stopped") {
        UploadState.phase = "stopped";
        renderProgress(100, "Διακόπηκε.");
        disableControls();
        stopPhasePolling();
        setTimeout(hideUploadPopup, 1500);
        return;
      }

      if (backendPhase === "done") {
        UploadState.phase = "done";
        renderProgress(100, "Ολοκληρώθηκε!");
        disableControls();
        stopPhasePolling();
        setTimeout(hideUploadPopup, 1500);
        return;
      }

      if (backendPhase === "upload") {
        UploadState.phase = "upload";
        const p = Math.max(1, Math.min(100, UploadState.lastUploadPercent || 1));
        renderProgress(p, "Uploading ZIP...");
        disableControls();
        return;
      }

      if (backendPhase === "unzip") {
        UploadState.phase = "unzip";
        const zp = Number.isFinite(data.zip_progress) ? data.zip_progress : 0;
        renderProgress(Math.max(1, zp), "Unzipping files...");
        disableControls();
        return;
      }

      if (backendPhase === "processing") {
        UploadState.phase = "processing";
        isPaused = data.status === "paused";
        enableControls();
        renderProgress(
          Math.max(1, data.progress || 1),
          isPaused ? "Σε παύση..." : "Processing XML..."
        );
      }
    } catch (e) {
      console.error("Phase poll error:", e);
    }
  }, 500);
}

/* ================= DUPLICATE MODAL ================= */

function showDuplicateModal(message) {
  $("duplicateModalMessage").textContent =
    message || "Το αρχείο υπάρχει ήδη. Θέλετε να το ανεβάσετε ξανά;";
  $("duplicateModal").style.display = "flex";
}

function hideDuplicateModal() {
  $("duplicateModal").style.display = "none";
}

/* ================= CORE UPLOAD ================= */

async function startUpload(file, force = false) {
  stopPhasePolling();
  isPaused = false;
  userStopped = false;

  UploadState.phase = "upload";
  UploadState.progress = 0;
  UploadState.lastUploadPercent = 1;

  disableControls();
  renderProgress(1, "Uploading ZIP...");
  showUploadPopup();
  startPhasePolling();

  const CHUNK_SIZE = 20 * 1024 * 1024;
  const totalChunks = Math.ceil(file.size / CHUNK_SIZE);
  const uploadId = crypto.randomUUID();

  for (let index = 0; index < totalChunks; index++) {
    const start = index * CHUNK_SIZE;
    const end = Math.min(start + CHUNK_SIZE, file.size);
    const chunk = file.slice(start, end);

    const formData = new FormData();
    formData.append("chunk", chunk);
    formData.append("upload_id", uploadId);
    formData.append("filename", file.name);
    formData.append("index", index);
    formData.append("total", totalChunks);
    formData.append("force", force ? "true" : "false");

    const res = await fetch("/upload_zip_chunk", {
      method: "POST",
      body: formData
    });

    const data = await res.json();

    if (data.already_exists && !force) {
      stopPhasePolling();
      hideUploadPopup();
      pendingFile = file;
      showDuplicateModal(data.message);
      return;
    }

    const percent = ((index + 1) / totalChunks) * 100;
    UploadState.lastUploadPercent = percent;
    renderProgress(percent, "Uploading ZIP...");
  }
}

/* ================= EVENTS ================= */

document.addEventListener("DOMContentLoaded", () => {
  const uploadBtn = $("uploadBtn");
  if (!uploadBtn) return;

  // hidden file input
  const zipInput = document.createElement("input");
  zipInput.type = "file";
  zipInput.accept = ".zip";
  zipInput.style.display = "none";
  document.body.appendChild(zipInput);

  // open file chooser
  uploadBtn.onclick = () => zipInput.click();

  // start upload
  zipInput.onchange = () => {
    const file = zipInput.files[0];
    if (file) startUpload(file, false);
  };

  /* ================= DUPLICATE MODAL ================= */

  // ❌ ΟΧΙ → δεν ανεβάζουμε, καθαρίζουμε state
  $("duplicateNo")?.addEventListener("click", async (e) => {
    e.preventDefault();

    pendingFile = null;
    hideDuplicateModal();

    // 🔑 καθαρίζουμε ΚΑΙ το backend
    try {
      await fetch("/reset_upload_state", { method: "POST" });
    } catch (err) {
      console.warn("reset_upload_state failed", err);
    }
  });

  // ✅ ΝΑΙ → ανεβάζουμε ξανά (force)
  $("duplicateYes")?.addEventListener("click", async (e) => {
    e.preventDefault();
    hideDuplicateModal();

    if (!pendingFile) return;

    const f = pendingFile;
    pendingFile = null;

    await startUpload(f, true); // force = true
  });
});


/* ================= RESTORE AFTER REFRESH ================= */

(async function restoreProgressIfNeeded() {
  try {
    const res = await fetch("/get_progress", { cache: "no-store" });
    const data = await res.json();

    if (!data.phase || data.phase === "idle" || data.phase === "done") return;

    showUploadPopup();
    startPhasePolling();

    if (data.phase === "upload") renderProgress(1, "Uploading ZIP...");
    if (data.phase === "unzip") renderProgress(1, "Unzipping files...");
    if (data.phase === "processing") renderProgress(1, "Processing XML...");
  } catch (e) {
    console.error("Restore progress failed", e);
  }
})();
