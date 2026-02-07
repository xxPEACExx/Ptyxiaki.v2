
document.addEventListener("DOMContentLoaded", () => {
  // ====== ΓΕΝΙΚΑ ELEMENTS ======
  const uploadBtn = document.querySelector(".button-33");
  const sidebar = document.getElementById("sidebar");
  const content = document.getElementById("content");
  const leftZone = document.getElementById("left-zone");
  const themeToggle = document.getElementById("themeToggle");
  const backBtn = document.getElementById("backBtn");
  const forwardBtn = document.getElementById("forwardBtn");
  const breadcrumbs = document.getElementById("breadcrumbs");

  // ====== ΚΑΤΑΣΤΑΣΗ FILE EXPLORER ======
  let currentPath = "";
  let backStack = [];
  let forwardStack = [];

  // ====== UPLOAD FOLDER ======
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

      loadFiles(currentPath || "");
    } catch (err) {
      console.error(err);
      alert("Σφάλμα κατά το ανέβασμα");
    }
  });

  // ====== FILE EXPLORER (get_files) ======
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
          row.addEventListener("click", () => enterFolder(item.path));
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
    if (!backBtn || !forwardBtn) return;
    backBtn.disabled = backStack.length === 0;
    forwardBtn.disabled = forwardStack.length === 0;
  }

  function updateBreadcrumbs() {
    if (!breadcrumbs) return;

    breadcrumbs.innerHTML = "";

    const parts = currentPath ? currentPath.split("/") : [];

    addBreadcrumb(breadcrumbs, "Αρχεία", "", parts.length === 0);

    let accumulated = "";
    parts.forEach((part, index) => {
      breadcrumbs.appendChild(createSeparator());
      accumulated += (index === 0 ? "" : "/") + part;
      addBreadcrumb(
        breadcrumbs,
        part,
        accumulated,
        index === parts.length - 1
      );
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

  if (backBtn) backBtn.addEventListener("click", goBack);
  if (forwardBtn) forwardBtn.addEventListener("click", goForward);

  // Στην information.html πιθανόν δεν υπάρχει fileList – δεν πειράζει.
  loadFiles("");

  // ====== THEME TOGGLE ======
  if (themeToggle) {
    const savedTheme = localStorage.getItem("theme");
    if (savedTheme === "dark") {
      document.body.classList.add("dark-theme");
      themeToggle.textContent = "🔆";
    }

    themeToggle.addEventListener("click", () => {
      const isDark = document.body.classList.toggle("dark-theme");
      themeToggle.textContent = isDark ? "🔆" : "🌓";
      localStorage.setItem("theme", isDark ? "dark" : "light");
    });
  }

  // ====== SIDEBAR AUTO-COLLAPSE ======
  if (sidebar && content && leftZone) {
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
  }

  // ==========================================
  // ############   APEXCHARTS   ###############
  // ==========================================
  if (typeof ApexCharts !== "undefined") {

    // === WEEKLY UPLOAD STATS (το παλιό γράφημα που δούλευε) ===
    fetch("/stats/uploads_per_week")
      .then(r => {
        if (!r.ok) throw new Error("HTTP error " + r.status);
        return r.json();
      })
      .then(realStats => {
        const chartMainEl = document.querySelector("#chart-main");
        if (!chartMainEl) return;

        const mainOptions = {
          chart: {
            type: "area",
            height: 260,
            toolbar: { show: false },
            zoom: { enabled: false }
          },
          series: [
            {
              name: "Files Uploaded",
              data: realStats.counts   // REAL DATA (εβδομάδες)
            }
          ],
          stroke: { curve: "smooth", width: 3 },
          dataLabels: { enabled: false },
          legend: { show: true, position: "top", horizontalAlign: "left" },
          xaxis: {
            categories: realStats.labels,   // REAL LABELS (Εβδ. 1–12)
            labels: { style: { fontSize: "11px" } },
            axisBorder: { show: false }
          },
          yaxis: {
            labels: { style: { fontSize: "11px" } },
            min: 0
          },
          grid: {
            borderColor: "#e5e7eb",
            strokeDashArray: 4
          },
          colors: ["#fb923c"],
          fill: {
            type: "gradient",
            gradient: {
              shadeIntensity: 0.9,
              opacityFrom: 0.3,
              opacityTo: 0.02,
              stops: [0, 80, 100]
            }
          },
          tooltip: { theme: "light" }
        };

        const mainChart = new ApexCharts(chartMainEl, mainOptions);
        mainChart.render();
      })
      .catch(err => {
        console.error("Σφάλμα στο fetch /stats/uploads_per_week:", err);
      });

    // === BAR CHART: ΔΗΜΟΣΙΕΥΣΕΙΣ ΑΝΑ ΜΗΝΑ ===
    const chartBarEl = document.querySelector("#chart-bar");
    if (chartBarEl) {
      fetch("/stats/uploads_per_month")
        .then(r => {
          if (!r.ok) throw new Error("HTTP error " + r.status);
          return r.json();
        })
        .then(monthStats => {
          const barOptions = {
            chart: { type: "bar", height: 190, toolbar: { show: false } },
            series: [
              {
                name: `Δημοσιεύσεις (${monthStats.year})`,
                data: monthStats.counts || []
              }
            ],
            xaxis: {
              categories: monthStats.labels || [],
              labels: { style: { fontSize: "10px" } },
              axisBorder: { show: false },
              axisTicks: { show: false }
            },
            plotOptions: { bar: { borderRadius: 6, columnWidth: "42%" } },
            yaxis: { labels: { style: { fontSize: "10px" } } },
            grid: { borderColor: "#e5e7eb", strokeDashArray: 4 },
            colors: ["#111827"],
            dataLabels: { enabled: false },
            tooltip: { theme: "light" }
          };

          new ApexCharts(chartBarEl, barOptions).render();
        })
        .catch(err => {
          console.error("Σφάλμα στο fetch /stats/uploads_per_month:", err);
        });
    }

    // === RADIAL CHART (διορθωμένο) ===
const chartRadialEl = document.querySelector("#chart-radial");
if (chartRadialEl) {
  const radialOptions = {
    chart: {
      type: "radialBar",
      height: 230
    },
    series: [100, 100, 100, 100],
    labels: ["Data Collection", "Analysis & Processing", "Visualization", "Statistical Overview"],
    plotOptions: {
      radialBar: {
        hollow: {
          size: "34%"
        },
        dataLabels: {
          name: {
            fontSize: "10px"
          },
          value: {
            fontSize: "14px",
            formatter: val => {

            }
          },
          total: {
            show: true,
            label: "Statistical Overview",
            fontSize: "10px",
            formatter: w => {
              const arr = w.globals.seriesTotals;
              const avg = arr.reduce((a, b) => a + b, 0) / arr.length;

              // αν το σύνολο είναι 100%, μην εμφανίζεται

            }
          }
        }
      }
    },
    colors: ["#fb923c", "#6366f1", "#10b981", "#0ea5e9"]
  };

  new ApexCharts(chartRadialEl, radialOptions).render();
}

  }
});
