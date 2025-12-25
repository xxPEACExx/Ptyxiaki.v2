//javasript mono gia to ulload tou index kai to ui po

//krivei to popup
function showUploadPopup() {
    document.getElementById("upload-popup").classList.remove("hidden");
}

function hideUploadPopup() {
    document.getElementById("upload-popup").classList.add("hidden");
}

function updateUploadProgress(percent) {
    const max = 219;
    const circle = document.getElementById("progress-circle");

    if (circle) {
        circle.style.strokeDashoffset = max - (percent / 100) * max;
    }
    const pct = document.getElementById("upload-percent");
    if (pct) pct.innerText = percent + "%";
}



//mas enimeronei gia thn proodo tou upload
let isPaused = false;
let processingInterval = null;

function startProcessingProgress() {
    const status = document.getElementById("upload-status");
    const pauseBtn = document.getElementById("pause-btn");
    const stopBtn = document.getElementById("stop-btn");

    pauseBtn.disabled = false;
    stopBtn.disabled = false;

    if (processingInterval) clearInterval(processingInterval);

    processingInterval = setInterval(async () => {
        const res = await fetch("/get_progress");
        const data = await res.json();

        updateUploadProgress(data.progress ?? 0);

        if (data.status === "paused") {
            status.textContent = "Σε παύση...";
        } else if (data.status === "running") {
            status.textContent = "Proccesing XML...";
        }

        if (data.progress >= 100 || data.status === "stopped") {
            clearInterval(processingInterval);

            status.textContent =
                data.status === "stopped" ? "Διακόπηκε." : "Ολοκληρώθηκε!";

            pauseBtn.disabled = true;
            stopBtn.disabled = true;

            setTimeout(hideUploadPopup, 2000);

            loadFiles("");
            updateCards();
        }
    }, 500);

    pauseBtn.onclick = async () => {
        if (!isPaused) {
            await fetch("/control", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ action: "pause" })
            });
            pauseBtn.textContent = "▶️ Συνέχεια";
            isPaused = true;
        } else {
            await fetch("/control", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ action: "continue" })
            });
            pauseBtn.textContent = "⏸ Παύση";
            isPaused = false;
        }
    };

    stopBtn.onclick = async () => {
        await fetch("/control", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ action: "stop" })
        });

        clearInterval(processingInterval);
        status.textContent = "Διακόπηκε.";

        setTimeout(hideUploadPopup, 1500);
    };
}



//anevasma arxeiou kai mono zip
document.addEventListener("DOMContentLoaded", () => {
    const uploadBtn = document.querySelector(".button-33");
    const cardsSection = document.querySelector("section.cards");

    const zipInput = document.createElement("input");
    zipInput.type = "file";
    zipInput.accept = ".zip, .7z";
    zipInput.style.display = "none";
    document.body.appendChild(zipInput);

    if (uploadBtn) {
        uploadBtn.addEventListener("click", () => zipInput.click());
    }

    // ZIP
    zipInput.addEventListener("change", async () => {
        const file = zipInput.files[0];
        if (!file) return;

        const ext = file.name.toLowerCase();
        if (!(ext.endsWith(".zip") || ext.endsWith(".7z"))) {
            alert("Μπορείτε να ανεβάσετε μόνο ZIP ή 7z αρχεία.");
            return;
        }

        const formData = new FormData();
        formData.append("files", file);

        showUploadPopup();
        document.getElementById("upload-title").textContent = "Upload...";
        document.getElementById("upload-status").textContent = "Upload ZIP/7z...";
        updateUploadProgress(0);

        const xhr = new XMLHttpRequest();
        xhr.open("POST", "/upload_zip");

        xhr.upload.onprogress = (e) => {
            if (e.lengthComputable) {
                updateUploadProgress(Math.round(e.loaded / e.total * 100));
            }
        };


        xhr.onload = () => {
            document.getElementById("upload-status").textContent = "Unpiz ZIP...";
            startZipProgress();   // ξεκινά η πρόοδος unzip
        };

        xhr.onerror = () => {
            document.getElementById("upload-status").textContent = "Σφάλμα κατά το ανέβασμα!";
            setTimeout(hideUploadPopup, 2000);
        };

        xhr.send(formData);
    });


    async function updateCards() {
        try {
            const res = await fetch("/get_documents");
            if (!res.ok) return;

            const data = await res.json();
            cardsSection.innerHTML = "";

            data.results.forEach(doc => {
                const card = document.createElement("div");
                card.classList.add("card");
                card.innerHTML = `
                    <h3>${doc.did}</h3>
                    <p>${doc.filepath || "Άγνωστο path"}</p>
                    <p style="color:green;">✔️ Ανέβηκε</p>
                `;
                cardsSection.prepend(card);
            });
        } catch (err) {
            console.error("Error fetching documents:", err);
        }
    }

    setInterval(updateCards, 1000);
    loadFiles("");
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




//file exlorer xekinaei edw

let currentPath = "";
let backStack = [];
let forwardStack = [];

async function loadFiles(path = "") {
    const list = document.getElementById("fileList");
    if (!list) return;

    try {
        const res = await fetch(`/get_files?path=${encodeURIComponent(path)}`);
        const files = await res.json();
        currentPath = path;

        list.innerHTML = "";

        files.forEach(item => {
            const row = document.createElement("div");
            row.className = "file-row";

            const icon = item.type === "folder" ? "📁" : "📄";

            row.innerHTML = `
                <span class="file-name">
                    <span class="file-icon">${icon}</span>
                    ${item.name}
                </span>
                <span>${item.type}</span>
                <span><span class="check-icon">✓</span></span>
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
        updateButtons();

    } catch (err) {
        console.error("Load error:", err);
    }
}

// Το navigation ston file explorer kai to breadcrumbs pou krataei tin diadromi
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

document.addEventListener("DOMContentLoaded", () => {
    const backBtn = document.getElementById("backBtn");
    const forwardBtn = document.getElementById("forwardBtn");

    if (backBtn) backBtn.addEventListener("click", goBack);
    if (forwardBtn) forwardBtn.addEventListener("click", goForward);
});

function updateBreadcrumbs() {
    const bc = document.getElementById("breadcrumbs");
    bc.innerHTML = "";

    const parts = currentPath ? currentPath.split("/") : [];
    addBreadcrumb(bc, "root", "", parts.length === 0);

    let accumulated = "";

    parts.forEach((part, i) => {
        bc.appendChild(createSeparator());
        accumulated += (i === 0 ? "" : "/") + part;
        addBreadcrumb(bc, part, accumulated, i === parts.length - 1);
    });
}

function addBreadcrumb(container, label, path, isLast) {
    const span = document.createElement("span");
    span.textContent = label;
    span.classList.add("bc-item");

    if (!isLast) {
        span.onclick = () => {
            backStack.push(currentPath);
            forwardStack = [];
            loadFiles(path);
        };
    } else {
        span.style.fontWeight = "600";
        span.style.color = "#ffffff";
    }

    container.appendChild(span);
}

function createSeparator() {
    const sep = document.createElement("span");
    sep.textContent = "›";
    sep.classList.add("separator");
    return sep;
}




// hover gia to sidebar
document.addEventListener("DOMContentLoaded", () => {
    const sidebar = document.getElementById("sidebar");
    const content = document.getElementById("content");
    const leftZone = document.getElementById("left-zone");

    setTimeout(() => {
        sidebar.classList.add("hidden");
        content.classList.add("expanded");
    }, 8000);

    leftZone.addEventListener("mouseenter", () => {
        sidebar.classList.remove("hidden");
        content.classList.remove("expanded");
    });

    sidebar.addEventListener("mouseleave", () => {
        sidebar.classList.add("hidden");
        content.classList.add("expanded");
    });
});



document.addEventListener("DOMContentLoaded", function () {
    const text = "Εδώ μπορείτε να να πλοηγηθείτε σε φακέλους, και στα τελικά αρχεία xml";
    const output = document.getElementById("output");
    const delay = 25;
    const restartDelay = 30000;

    function typeWriter(i = 0) {
        if (i < text.length) {
            output.textContent += text.charAt(i);
            setTimeout(() => typeWriter(i + 1), delay);
        } else {
            setTimeout(() => {
                output.textContent = "";
                typeWriter();
            }, restartDelay);
        }
    }

    typeWriter();
});




function startZipProgress() {
    const status = document.getElementById("upload-status");
    status.textContent = "Unzip ZIP...";

    const interval = setInterval(async () => {
        const res = await fetch("/zip_progress");
        const data = await res.json();

        const percent = data.progress ?? 0;
        updateUploadProgress(percent);

        if (percent >= 100) {
            clearInterval(interval);
            status.textContent = "Proccesing XML...";
            startProcessingProgress();
        }

    }, 400);
}
