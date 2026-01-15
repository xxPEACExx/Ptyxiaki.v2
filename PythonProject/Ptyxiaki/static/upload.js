//// =====================================================
//// GLOBAL STATE
//// =====================================================
//let isPaused = false;
//let userStopped = false;
//let zipInterval = null;
//let processingInterval = null;
//
//const UploadState = {
//    phase: "idle", // idle | upload | unzip | processing | done | stopped
//    progress: 0
//};
//
//// =====================================================
//// POPUP UI
//// =====================================================
//function showUploadPopup() {
//    document.getElementById("upload-popup")?.classList.remove("hidden");
//}
//
//function hideUploadPopup() {
//    document.getElementById("upload-popup")?.classList.add("hidden");
//}
//
//function updateUploadProgress(percent) {
//    const circle = document.getElementById("progress-circle");
//    if (!circle) return;
//
//    const max = circle.getTotalLength ? circle.getTotalLength() : 219;
//    circle.style.strokeDashoffset = max - (percent / 100) * max;
//
//    const pct = document.getElementById("upload-percent");
//    if (pct) pct.innerText = Math.round(percent) + "%";
//}
//
//function renderProgress(percent, text) {
//    UploadState.progress = percent;
//    updateUploadProgress(percent);
//    if (text) {
//        const status = document.getElementById("upload-status");
//        if (status) status.textContent = text;
//    }
//}
//
//// =====================================================
//// WAIT FOR BACKEND PHASE
//// =====================================================
//function waitForPhase(targetPhase, callback) {
//    const poll = setInterval(async () => {
//        const res = await fetch("/get_progress");
//        const data = await res.json();
//
//        if (data.phase === targetPhase) {
//            clearInterval(poll);
//            callback();
//        }
//    }, 300);
//}
//
//// =====================================================
//// PROCESSING (XML)
//// =====================================================
//function startProcessingProgress() {
//    if (processingInterval) return;
//
//    UploadState.phase = "processing";
//
//    const pauseBtn = document.getElementById("pause-btn");
//    const stopBtn = document.getElementById("stop-btn");
//
//    isPaused = false;
//    userStopped = false;
//
//    pauseBtn.disabled = false;
//    stopBtn.disabled = false;
//    pauseBtn.textContent = "⏸ Παύση";
//
//    pauseBtn.onclick = async () => {
//        const action = isPaused ? "continue" : "pause";
//        await fetch("/control", {
//            method: "POST",
//            headers: { "Content-Type": "application/json" },
//            body: JSON.stringify({ action })
//        });
//        isPaused = !isPaused;
//        pauseBtn.textContent = isPaused ? "▶️ Συνέχεια" : "⏸ Παύση";
//    };
//
//    stopBtn.onclick = async () => {
//        userStopped = true;
//        await fetch("/control", {
//            method: "POST",
//            headers: { "Content-Type": "application/json" },
//            body: JSON.stringify({ action: "stop" })
//        });
//    };
//
//    processingInterval = setInterval(async () => {
//        const res = await fetch("/get_progress");
//        const data = await res.json();
//
//        if (data.phase === "processing") {
//            renderProgress(
//                data.progress ?? 0,
//                data.status === "paused"
//                    ? "Σε παύση..."
//                    : "Processing XML..."
//            );
//        }
//
//        if (data.phase === "done" || data.phase === "stopped") {
//            clearInterval(processingInterval);
//            processingInterval = null;
//
//            pauseBtn.disabled = true;
//            stopBtn.disabled = true;
//
//            renderProgress(
//                100,
//                data.phase === "stopped"
//                    ? "Διακόπηκε."
//                    : "Ολοκληρώθηκε!"
//            );
//
//            loadFiles("");
//            updateCards();
//
//            setTimeout(hideUploadPopup, 1500);
//        }
//    }, 500);
//}
//
//// =====================================================
//// ZIP UNZIP
//// =====================================================
//function startZipProgress() {
//    if (zipInterval) clearInterval(zipInterval);
//
//    UploadState.phase = "unzip";
//
//    zipInterval = setInterval(async () => {
//    const res = await fetch("/zip_progress");
//    const data = await res.json();
//
//    // FORCE label αλλαγή
//    renderProgress(
//        UploadState.progress > 1 ? UploadState.progress : 1,
//        "Unzipping files..."
//    );
//
//    if (!data.total) {
//        return;
//    }
//
//    const percent = data.progress ?? 0;
//    renderProgress(percent, "Unzipping files...");
//
//    if (percent >= 100) {
//        clearInterval(zipInterval);
//        zipInterval = null;
//        waitForPhase("processing", startProcessingProgress);
//    }
//}, 400);
//
//}
//
//// =====================================================
//// FILE UPLOAD (CHUNKED, NO OTHER CHANGES)
//// =====================================================
//document.addEventListener("DOMContentLoaded", () => {
//    const uploadBtn = document.querySelector(".button-33");
//    const cardsSection = document.querySelector("section.cards");
//
//    const zipInput = document.createElement("input");
//    zipInput.type = "file";
//    zipInput.accept = ".zip";
//    zipInput.style.display = "none";
//    document.body.appendChild(zipInput);
//
//    uploadBtn?.addEventListener("click", () => zipInput.click());
//
//    zipInput.addEventListener("change", async () => {
//        const file = zipInput.files[0];
//        if (!file) return;
//
//        if (processingInterval) clearInterval(processingInterval);
//        if (zipInterval) clearInterval(zipInterval);
//
//        isPaused = false;
//        userStopped = false;
//
//        renderProgress(0, "Preparing upload...");
//        showUploadPopup();
//
//        if (!file.name.toLowerCase().endsWith(".zip")) {
//            alert("Μόνο ZIP αρχεία.");
//            return;
//        }
//
//        UploadState.phase = "upload";
//
//        const CHUNK_SIZE = 20 * 1024 * 1024; // 20MB
//        const totalChunks = Math.ceil(file.size / CHUNK_SIZE);
//
//        const uploadId = crypto.randomUUID();
//
//        for (let index = 0; index < totalChunks; index++) {
//            const start = index * CHUNK_SIZE;
//            const end = Math.min(start + CHUNK_SIZE, file.size);
//            const chunk = file.slice(start, end);
//
//            const formData = new FormData();
//            formData.append("chunk", chunk);
//            formData.append("upload_id", uploadId);
//            formData.append("filename", file.name);
//            formData.append("index", index);
//            formData.append("total", totalChunks);
//
//            const res = await fetch("/upload_zip_chunk", {
//                method: "POST",
//                body: formData
//            });
//
//            if (!res.ok) {
//                renderProgress(0, "Σφάλμα στο upload.");
//                return;
//            }
//
//            const percent = ((index + 1) / totalChunks) * 100;
//            renderProgress(percent, "Uploading ZIP...");
//        }
//
//        renderProgress(1, "Ξεκίνησε το unzip...");
//        UploadState.phase = "unzip";
//        startZipProgress();
//    });
//
//    // =====================================================
//    // UPDATE CARDS
//    // =====================================================
//    async function updateCards() {
//        const res = await fetch("/get_documents");
//        if (!res.ok) return;
//
//        const data = await res.json();
//        cardsSection.innerHTML = "";
//
//        data.results.forEach(doc => {
//            const card = document.createElement("div");
//            card.className = "card";
//            card.innerHTML = `
//                <h3>${doc.did}</h3>
//                <p>${doc.filepath || "Άγνωστο path"}</p>
//                <p style="color:green;">✔️ Ανέβηκε</p>
//            `;
//            cardsSection.prepend(card);
//        });
//    }
//
//    setInterval(updateCards, 1000);
//    loadFiles("");
//});
//
//
//// =====================================================
//// THEME TOGGLE
//// =====================================================
//document.addEventListener("DOMContentLoaded", () => {
//    const btn = document.getElementById("themeToggle");
//    const body = document.body;
//
//    if (localStorage.getItem("theme") === "dark") {
//        body.classList.add("dark-theme");
//        btn.textContent = "🔆";
//    }
//
//    btn.onclick = () => {
//        const dark = body.classList.toggle("dark-theme");
//        btn.textContent = dark ? "🔆" : "🌓";
//        localStorage.setItem("theme", dark ? "dark" : "light");
//    };
//});
//
//// =====================================================
//// FILE EXPLORER + BREADCRUMBS
//// =====================================================
//let currentPath = "";
//let backStack = [];
//let forwardStack = [];
//
//async function loadFiles(path = "") {
//    const list = document.getElementById("fileList");
//    if (!list) return;
//
//    const res = await fetch(`/get_files?path=${encodeURIComponent(path)}`);
//    const files = await res.json();
//
//    currentPath = path;
//    list.innerHTML = "";
//
//    files.forEach(item => {
//        const row = document.createElement("div");
//        row.className = "file-row";
//
//        row.innerHTML = `
//            <span class="file-name">
//                <span class="file-icon">${item.type === "folder" ? "📁" : "📄"}</span>
//                ${item.name}
//            </span>
//            <span>${item.type}</span>
//            <span>✓</span>
//            <span>${item.date || "-"}</span>
//            <span class="menu">⋮</span>
//        `;
//
//        if (item.type === "folder") {
//            row.onclick = () => {
//                backStack.push(currentPath);
//                forwardStack = [];
//                loadFiles(item.path);
//            };
//        }
//
//        list.appendChild(row);
//    });
//
//    updateBreadcrumbs();
//}
//
//// =====================================================
//// BREADCRUMBS + NAV
//// =====================================================
//function goBack() {
//    if (!backStack.length) return;
//    forwardStack.push(currentPath);
//    loadFiles(backStack.pop());
//}
//
//function goForward() {
//    if (!forwardStack.length) return;
//    backStack.push(currentPath);
//    loadFiles(forwardStack.pop());
//}
//
//function updateBreadcrumbs() {
//    const bc = document.getElementById("breadcrumbs");
//    bc.innerHTML = "";
//
//    const parts = currentPath ? currentPath.split("/") : [];
//    addBreadcrumb(bc, "root", "", parts.length === 0);
//
//    let acc = "";
//    parts.forEach((p, i) => {
//        bc.append("›");
//        acc += (i ? "/" : "") + p;
//        addBreadcrumb(bc, p, acc, i === parts.length - 1);
//    });
//}
//
//function addBreadcrumb(container, label, path, isLast) {
//    const span = document.createElement("span");
//    span.textContent = label;
//    span.className = "bc-item";
//    if (!isLast) span.onclick = () => loadFiles(path);
//    container.appendChild(span);
//}
//
//// =====================================================
//// SIDEBAR HOVER
//// =====================================================
//document.addEventListener("DOMContentLoaded", () => {
//    const sidebar = document.getElementById("sidebar");
//    const content = document.getElementById("content");
//    const leftZone = document.getElementById("left-zone");
//
//    setTimeout(() => {
//        sidebar.classList.add("hidden");
//        content.classList.add("expanded");
//    }, 8000);
//
//    leftZone.onmouseenter = () => {
//        sidebar.classList.remove("hidden");
//        content.classList.remove("expanded");
//    };
//
//    sidebar.onmouseleave = () => {
//        sidebar.classList.add("hidden");
//        content.classList.add("expanded");
//    };
//});
//
//// =====================================================
//// TYPEWRITER
//// =====================================================
//document.addEventListener("DOMContentLoaded", () => {
//    const text = "Εδώ μπορείτε να να πλοηγηθείτε σε φακέλους, και στα τελικά αρχεία xml";
//    const output = document.getElementById("output");
//    let i = 0;
//
//    (function type() {
//        if (!output) return;
//        if (i < text.length) {
//            output.textContent += text[i++];
//            setTimeout(type, 25);
//        } else {
//            setTimeout(() => {
//                output.textContent = "";
//                i = 0;
//                type();
//            }, 30000);
//        }
//    })();
//});
//
//(async function restoreProgressIfNeeded() {
//    try {
//        const res = await fetch("/get_progress");
//        const data = await res.json();
//
//        if (!data.phase || data.phase === "idle" || data.phase === "done") {
//            return;
//        }
//
//        showUploadPopup();
//
//        if (data.phase === "upload") {
//            renderProgress(10, "Uploading ZIP...");
//        }
//
//        if (data.phase === "unzip" && UploadState.phase !== "unzip") {
//        UploadState.phase = "unzip";
//        renderProgress(1, "Ξεκίνησε το unzip...");
//        startZipProgress();
//        }
//
//
//        if (data.phase === "processing") {
//            startProcessingProgress();
//        }
//
//    } catch (e) {
//        console.error("Restore progress failed", e);
//    }
//})();

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

            if (!res.ok) {
                renderProgress(1, "Σφάλμα στο upload.");
                stopPhasePolling();
                setTimeout(hideUploadPopup, 2000);
                return;
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
    const text = "Εδώ μπορείτε να να πλοηγηθείτε σε φακέλους, και στα τελικά αρχεία xml";
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
            }, 30000);
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
