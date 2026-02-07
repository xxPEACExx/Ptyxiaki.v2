

// =====================================================
// GLOBAL STATE
// =====================================================
let isPaused = false;
let userStopped = false;

let phasePollInterval = null;

const UploadState = {
    phase: "idle", // idle | upload | unzip | processing | done | stopped
    progress: 0,
    lastUploadPercent: 0
};

// =====================================================
// POPUP UI
// =====================================================
function showUploadPopup() {
    document.getElementById("upload-popup")?.classList.remove("hidden");
}

function hideUploadPopup() {
    document.getElementById("upload-popup")?.classList.add("hidden");
}

function updateUploadProgress(percent) {
    const circle = document.getElementById("progress-circle");
    if (!circle) return;

    const max = circle.getTotalLength ? circle.getTotalLength() : 219;
    circle.style.strokeDashoffset = max - (percent / 100) * max;

    const pct = document.getElementById("upload-percent");
    if (pct) pct.innerText = Math.round(percent) + "%";
}

function renderProgress(percent, text) {
    UploadState.progress = percent;
    updateUploadProgress(percent);

    if (text) {
        const status = document.getElementById("upload-status");
        if (status) status.textContent = text;
    }
}

// =====================================================
// BACKEND PHASE POLL (single source of truth)
// =====================================================
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

            // STOPPED / DONE have priority
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
                loadFiles("");
                updateCards();
                setTimeout(hideUploadPopup, 1500);
                return;
            }

            // =========================
            // UPLOAD PHASE (client-side %)
            // =========================
            if (backendPhase === "upload") {
                UploadState.phase = "upload";

                // Εδώ δεν βασιζόμαστε στο backend για % upload.
                // Κρατάμε το τελευταίο client-side percent.
                const p = Math.max(1, Math.min(100, UploadState.lastUploadPercent || 1));
                renderProgress(p, "Uploading ZIP...");
                return;
            }

            // =========================
            // UNZIP PHASE (backend zip_progress)
            // =========================
            if (backendPhase === "unzip") {
                UploadState.phase = "unzip";

                // zip_progress έρχεται από backend
                const zp = Number.isFinite(data.zip_progress) ? data.zip_progress : 0;

                // Θέλεις 1..100: ποτέ 0 στο UI
                const p = Math.max(1, Math.min(100, zp || 1));
                renderProgress(p, "Unzipping files...");
                return;
            }

            // =========================
            // PROCESSING PHASE (backend progress)
            // =========================
            if (backendPhase === "processing") {
                UploadState.phase = "processing";
                enableControls();

                const paused = data.status === "paused";
                const pr = Number.isFinite(data.progress) ? data.progress : 0;

                // Θέλεις 1..100: ποτέ 0 στο UI (εκτός αν όντως δεν έχει ξεκινήσει)
                const p = Math.max(1, Math.min(100, pr || 1));

                renderProgress(p, paused ? "Σε παύση..." : "Processing XML...");
                return;
            }

            // Fallback
            UploadState.phase = backendPhase;

        } catch (e) {
            // Δεν “σκοτώνουμε” UI σε transient error
            // αλλά κρατάμε το τελευταίο.
            console.error("Phase poll error:", e);
        }
    }, 500);
}

// =====================================================
// CONTROLS (Pause/Stop)
// =====================================================
function enableControls() {
    const pauseBtn = document.getElementById("pause-btn");
    const stopBtn = document.getElementById("stop-btn");
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
    const pauseBtn = document.getElementById("pause-btn");
    const stopBtn = document.getElementById("stop-btn");
    if (pauseBtn) pauseBtn.disabled = true;
    if (stopBtn) stopBtn.disabled = true;
}

// =====================================================
// FILE UPLOAD (CHUNKED)
// =====================================================
document.addEventListener("DOMContentLoaded", () => {
    const uploadBtn = document.querySelector(".button-33");
    const cardsSection = document.querySelector("section.cards");

    const zipInput = document.createElement("input");
    zipInput.type = "file";
    zipInput.accept = ".zip";
    zipInput.style.display = "none";
    document.body.appendChild(zipInput);

    uploadBtn?.addEventListener("click", () => zipInput.click());

    zipInput.addEventListener("change", async () => {
        const file = zipInput.files[0];
        if (!file) return;

        // reset UI state
        stopPhasePolling();
        isPaused = false;
        userStopped = false;
        UploadState.phase = "upload";
        UploadState.progress = 0;
        UploadState.lastUploadPercent = 1;

        disableControls();
        renderProgress(1, "Preparing upload...");
        showUploadPopup();

        if (!file.name.toLowerCase().endsWith(".zip")) {
            alert("Μόνο ZIP αρχεία.");
            hideUploadPopup();
            return;
        }

        // Start polling immediately so UI follows backend phase transitions
        startPhasePolling();

        const CHUNK_SIZE = 20 * 1024 * 1024; // 20MB
        const totalChunks = Math.ceil(file.size / CHUNK_SIZE);
        const uploadId = crypto.randomUUID();

        // During upload we want 1..100
        UploadState.lastUploadPercent = 1;
        renderProgress(1, "Uploading ZIP...");

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


            const res = await fetch("/upload_zip_chunk", {
    method: "POST",
    body: formData
});

// 1️⃣ HTTP-level error
if (!res.ok) {
    renderProgress(1, "Σφάλμα στο upload.");
    stopPhasePolling();
    setTimeout(hideUploadPopup, 2000);
    return;
}

// 2️⃣ Parse JSON
const data = await res.json();

// 3️⃣ Duplicate ZIP detected (μόνο στο index == 0 από backend)
if (data.already_exists) {
    stopPhasePolling();
    hideUploadPopup();
    showDuplicateModal(data.message || "Το αρχείο έχει ήδη ανέβει.");
    return; // ⛔ ΣΤΑΜΑΤΑΜΕ ΟΛΟ ΤΟ UPLOAD
}


            const percent = ((index + 1) / totalChunks) * 100;
            UploadState.lastUploadPercent = Math.max(1, Math.min(100, percent));
            renderProgress(UploadState.lastUploadPercent, "Uploading ZIP...");
        }

        // After last chunk sent, backend will move to unzip/processing.
        // We do NOT force UI here; polling will switch phase.
        renderProgress(100, "Upload ολοκληρώθηκε. Αναμονή για unzip...");
    });




    // =====================================================
    // UPDATE CARDS
    // =====================================================
    async function updateCards() {
        const res = await fetch("/get_documents");
        if (!res.ok) return;

        const data = await res.json();
        cardsSection.innerHTML = "";

        data.results.forEach(doc => {
            const card = document.createElement("div");
            card.className = "card";
            card.innerHTML = `
                <h3>${doc.did}</h3>
                <p>${doc.filepath || "Άγνωστο path"}</p>
                <p style="color:green;">✔️ Ανέβηκε</p>
            `;
            cardsSection.prepend(card);
        });
    }

    window.updateCards = updateCards; // used elsewhere
    setInterval(updateCards, 1000);
    loadFiles("");
});

// =====================================================
// THEME TOGGLE
// =====================================================
document.addEventListener("DOMContentLoaded", () => {
    const btn = document.getElementById("themeToggle");
    const body = document.body;

    if (localStorage.getItem("theme") === "dark") {
        body.classList.add("dark-theme");
        btn.textContent = "🔆";
    }

    btn.onclick = () => {
        const dark = body.classList.toggle("dark-theme");
        btn.textContent = dark ? "🔆" : "🌓";
        localStorage.setItem("theme", dark ? "dark" : "light");
    };
});

// =====================================================
// FILE EXPLORER + BREADCRUMBS
// =====================================================
let currentPath = "";
let backStack = [];
let forwardStack = [];

async function loadFiles(path = "") {
    const list = document.getElementById("fileList");
    if (!list) return;

    const res = await fetch(`/get_files?path=${encodeURIComponent(path)}`);
    const files = await res.json();

    currentPath = path;
    list.innerHTML = "";

    files.forEach(item => {
        const row = document.createElement("div");
        row.className = "file-row";

        row.innerHTML = `
            <span class="file-name">
                <span class="file-icon">${item.type === "folder" ? "📁" : "📄"}</span>
                ${item.name}
            </span>
            <span>${item.type}</span>
            <span>✓</span>
            <span>${item.date || "-"}</span>
            <span class="menu">⋮</span>
        `;

        if (item.type === "folder") {
            row.onclick = () => {
                backStack.push(currentPath);
                forwardStack = [];
                loadFiles(item.path);
            };
        }

        list.appendChild(row);
    });

    updateBreadcrumbs();
}

// =====================================================
// BREADCRUMBS + NAV
// =====================================================
function goBack() {
    if (!backStack.length) return;
    forwardStack.push(currentPath);
    loadFiles(backStack.pop());
}

function goForward() {
    if (!forwardStack.length) return;
    backStack.push(currentPath);
    loadFiles(forwardStack.pop());
}

function updateBreadcrumbs() {
    const bc = document.getElementById("breadcrumbs");
    if (!bc) return;

    bc.innerHTML = "";

    const parts = currentPath ? currentPath.split("/") : [];
    addBreadcrumb(bc, "root", "", parts.length === 0);

    let acc = "";
    parts.forEach((p, i) => {
        bc.append("›");
        acc += (i ? "/" : "") + p;
        addBreadcrumb(bc, p, acc, i === parts.length - 1);
    });
}

function addBreadcrumb(container, label, path, isLast) {
    const span = document.createElement("span");
    span.textContent = label;
    span.className = "bc-item";
    if (!isLast) span.onclick = () => loadFiles(path);
    container.appendChild(span);
}

// =====================================================
// SIDEBAR HOVER
// =====================================================
document.addEventListener("DOMContentLoaded", () => {
    const sidebar = document.getElementById("sidebar");
    const content = document.getElementById("content");
    const leftZone = document.getElementById("left-zone");

    setTimeout(() => {
        sidebar?.classList.add("hidden");
        content?.classList.add("expanded");
    }, 8000);

    if (leftZone && sidebar && content) {
        leftZone.onmouseenter = () => {
            sidebar.classList.remove("hidden");
            content.classList.remove("expanded");
        };

        sidebar.onmouseleave = () => {
            sidebar.classList.add("hidden");
            content.classList.add("expanded");
        };
    }
});

// =====================================================
// TYPEWRITER
// =====================================================
document.addEventListener("DOMContentLoaded", () => {
    const text = "Here you have a concise overview of your application and the data stored in the database. You can also navigate through folders and access the final XML files.";
    const output = document.getElementById("output");
    let i = 0;

    (function type() {
        if (!output) return;
        if (i < text.length) {
            output.textContent += text[i++];
            setTimeout(type, 25);
        } else {
            setTimeout(() => {
                output.textContent = "";
                i = 0;
                type();
            }, 300000);
        }
    })();
});

// =====================================================
// RESTORE PROGRESS ON PAGE LOAD
// =====================================================
(async function restoreProgressIfNeeded() {
    try {
        const res = await fetch("/get_progress", { cache: "no-store" });
        const data = await res.json();

        if (!data.phase || data.phase === "idle" || data.phase === "done") return;

        showUploadPopup();
        startPhasePolling();

        // Μην forceάρεις 100 εδώ. Το poll θα αναλάβει σωστά.
        if (data.phase === "upload") renderProgress(1, "Uploading ZIP...");
        if (data.phase === "unzip") renderProgress(1, "Unzipping files...");
        if (data.phase === "processing") renderProgress(1, "Processing XML...");

    } catch (e) {
        console.error("Restore progress failed", e);
    }
})();

function showDuplicateModal(message) {
  const modal = document.getElementById("duplicateModal");
  const msg = document.getElementById("duplicateModalMessage");

  if (msg) {
    msg.textContent = message || "Το αρχείο έχει ήδη ανέβει.";
  }

  if (modal) {
    modal.style.display = "flex";
  }
}

function hideDuplicateModal() {
  const modal = document.getElementById("duplicateModal");
  if (modal) {
    modal.style.display = "none";
  }
}

document.getElementById("duplicateModalOk")?.addEventListener("click", hideDuplicateModal);
