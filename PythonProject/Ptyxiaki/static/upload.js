
document.addEventListener("DOMContentLoaded", () => {
    const uploadBtn = document.querySelector(".button-33");
    const cardsSection = document.querySelector("section.cards");
    const progressText = document.getElementById("progress-text");

    const folderInput = document.createElement("input");
    folderInput.type = "file";
    folderInput.webkitdirectory = true;
    folderInput.multiple = true;
    folderInput.style.display = "none";
    document.body.appendChild(folderInput);

    if (uploadBtn) {
        uploadBtn.addEventListener("click", () => folderInput.click());
    }

    folderInput.addEventListener("change", async () => {
        const files = [...folderInput.files];
        if (!files.length) return;

        const formData = new FormData();
        files.forEach(f => formData.append("files", f));

        try {
            const res = await fetch("/upload_folder", {
                method: "POST",
                body: formData
            });

            const data = await res.json();
            alert(data.message || "Ξεκίνησε η επεξεργασία");

            loadFiles("");

            updateCards();

        } catch (err) {
            console.error(err);
            alert("Σφάλμα κατά το ανέβασμα");
        }
    });

    async function updateCards() {
        try {
            const res = await fetch("/get_documents");
            if (!res.ok) return;
            const data = await res.json();
            if (!cardsSection) return;

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

  if (!toggleBtn) return;

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



let currentPath = "";
let backStack = [];
let forwardStack = [];

async function loadFiles(path = "") {
    const list = document.getElementById("fileList");
    if (!list) return;

    try {
        const res = await fetch(`/get_files?path=${encodeURIComponent(path)}`);
        if (!res.ok) {
            console.error("get_files error");
            return;
        }

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
                row.style.cursor = "pointer";
                row.addEventListener("click", () => {
                    enterFolder(item.path);   // item.path έρχεται από backend
                });
            }

            list.appendChild(row);
        });

        updateBreadcrumbs();
        updateButtons();

    } catch (err) {
        console.error("Load error:", err);
    }
}


function enterFolder(targetPath) {
    backStack.push(currentPath);
    forwardStack = [];
    loadFiles(targetPath);
}


function goBack() {
    if (backStack.length === 0) return;
    forwardStack.push(currentPath);
    const prev = backStack.pop();
    loadFiles(prev);
}


function goForward() {
    if (forwardStack.length === 0) return;
    backStack.push(currentPath);
    const next = forwardStack.pop();
    loadFiles(next);
}


function updateButtons() {
    const backBtn = document.getElementById("backBtn");
    const forwardBtn = document.getElementById("forwardBtn");
    if (!backBtn || !forwardBtn) return;

    backBtn.disabled = backStack.length === 0;
    forwardBtn.disabled = forwardStack.length === 0;
}


function updateBreadcrumbs() {
    const bc = document.getElementById("breadcrumbs");
    if (!bc) return;

    bc.innerHTML = "";

    const parts = currentPath ? currentPath.split("/") : [];


    addBreadcrumb(bc, "Αρχεία", "", parts.length === 0);

    let accumulated = "";

    parts.forEach((part, index) => {
        bc.appendChild(createSeparator());

        accumulated += (index === 0 ? "" : "/") + part;

        addBreadcrumb(bc, part, accumulated, index === parts.length - 1);
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
        // Αν έχεις dark theme, άσπρο:
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


document.addEventListener("DOMContentLoaded", () => {
    const backBtn = document.getElementById("backBtn");
    const forwardBtn = document.getElementById("forwardBtn");

    if (backBtn) backBtn.addEventListener("click", goBack);
    if (forwardBtn) forwardBtn.addEventListener("click", goForward);

    updateButtons();
});

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

    const text = "Εδώ μπορείτε να να πλοηγηθείτε σε φακέλους (EP), και στα τελικά αρχεία xml" ;
    const output = document.getElementById("output");
    const delay = 25;          // h taxutita pou grafei
    const restartDelay = 30000; // Orisa 30 deuterolepta

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