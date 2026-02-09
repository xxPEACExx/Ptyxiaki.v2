//
//
//document.addEventListener("DOMContentLoaded", () => {
//  fetch("/api/overview")
//    .then(res => res.json())
//    .then(data => {
//      // Αριθμητικά cards
//      document.getElementById("total-docs").textContent = data.total_documents;
//      document.getElementById("unique-applicants").textContent = data.unique_applicants;
//      document.getElementById("max-claims").textContent = data.max_claims;
//      document.getElementById("languages-count").textContent = data.languages_count;
//      document.getElementById("docs-with-description").textContent = data.documents_with_description;
//      document.getElementById("multi-lang-titles").textContent = data.multilingual_titles;
//
//      // Εύρος ημερομηνιών
//      if (data.date_range.min && data.date_range.max) {
//        document.getElementById("date-range").textContent =
//          `${data.date_range.min} — ${data.date_range.max}`;
//      }
//
//      // Χώρες → donut
//      renderCountriesDonut(data.countries);
//    });
//});
//
//
//function renderCountriesDonut(countries) {
//  const ctx = document.getElementById("countriesChart").getContext("2d");
//
//  const labels = Object.keys(countries);
//  const values = Object.values(countries);
//
//  new Chart(ctx, {
//    type: "doughnut",
//    data: {
//      labels: labels,
//      datasets: [{
//        data: values,
//        backgroundColor: ["#3b82f6", "#22c55e", "#f59e0b", "#ef4444"]
//      }]
//    },
//    options: {
//      responsive: true,
//      plugins: {
//        legend: {
//          display: false
//        }
//      },
//      cutout: "65%"
//    }
//  });
//
//  // Legend text (EP – 100 κτλ)
//  const legend = document.getElementById("countriesLegend");
//  legend.innerHTML = labels
//    .map((l, i) => `${l} – ${values[i]}`)
//    .join(" | ");
//}

document.addEventListener("DOMContentLoaded", () => {
  fetch("/api/overview")
    .then(res => res.json())
    .then(data => {
      // =============================
      // Αριθμητικά stat cards
      // =============================
      document.getElementById("total-docs").textContent = data.total_documents ?? 0;
      document.getElementById("unique-applicants").textContent = data.unique_applicants ?? 0;
      document.getElementById("max-claims").textContent = data.max_claims ?? 0;
      document.getElementById("languages-count").textContent = data.languages_count ?? 0;
      document.getElementById("docs-with-description").textContent = data.documents_with_description ?? 0;
      document.getElementById("multi-lang-titles").textContent = data.multilingual_titles ?? 0;

      // 🆕 Φάκελοι
      const foldersEl = document.getElementById("folders-count");
      if (foldersEl) {
        foldersEl.textContent = data.folders_count ?? 0;
      }

      // =============================
      // Εύρος ημερομηνιών
      // =============================
      if (data.date_range?.min && data.date_range?.max) {
        const dr = document.getElementById("date-range");
        if (dr) {
          dr.textContent = `${data.date_range.min} — ${data.date_range.max}`;
        }
      }

      // =============================
      // Charts
      // =============================
      if (data.countries) {
        renderCountriesDonut(data.countries);
      }

      if (data.documents_per_year) {
        renderDocsPerYear(data.documents_per_year);
      }

      if (data.languages) {
        renderLanguagesChart(data.languages);
      }

      if (data.top_applicants) {
        renderTopApplicants(data.top_applicants);
      }
    })
    .catch(err => {
      console.error("Overview fetch failed:", err);
    });
});


// =====================================================
// DONUT: Countries
// =====================================================
function renderCountriesDonut(countries) {
  const canvas = document.getElementById("countriesChart");
  if (!canvas) return;

  const ctx = canvas.getContext("2d");

  const labels = Object.keys(countries);
  const values = Object.values(countries);

  new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: labels,
      datasets: [{
        data: values,
        backgroundColor: [
          "#3b82f6",
          "#22c55e",
          "#f59e0b",
          "#ef4444",
          "#8b5cf6",
          "#06b6d4"
        ]
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false }
      },
      cutout: "65%"
    }
  });

  const legend = document.getElementById("countriesLegend");
  if (legend) {
    legend.innerHTML = labels
      .map((l, i) => `${l} – ${values[i]}`)
      .join(" | ");
  }
}


// =====================================================
// BAR: Documents per Year
// =====================================================
function renderDocsPerYear(data) {
  const canvas = document.getElementById("docsPerYearChart");
  if (!canvas) return;

  new Chart(canvas, {
    type: "bar",
    data: {
      labels: Object.keys(data),
      datasets: [{
        data: Object.values(data)
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false }
      }
    }
  });
}


// =====================================================
// PIE: Languages Distribution
// =====================================================
function renderLanguagesChart(langs) {
  const canvas = document.getElementById("languagesChart");
  if (!canvas) return;

  new Chart(canvas, {
    type: "pie",
    data: {
      labels: Object.keys(langs),
      datasets: [{
        data: Object.values(langs)
      }]
    },
    options: {
      responsive: true
    }
  });
}


// =====================================================
// LIST: Top Applicants
// =====================================================
function renderTopApplicants(applicants) {
  const container = document.getElementById("topApplicantsList");
  if (!container) return;

  container.innerHTML = "";

  const entries = Object.entries(applicants);
  if (entries.length === 0) {
    container.textContent = "No applicants data";
    return;
  }

  entries.forEach(([name, count], index) => {
    const item = document.createElement("div");
    item.className = "applicant-item";

    const left = document.createElement("div");
    left.className = "applicant-left";

    const rank = document.createElement("div");
    rank.className = "applicant-rank";
    rank.textContent = index + 1;

    const nameEl = document.createElement("div");
    nameEl.className = "applicant-name";
    nameEl.textContent = name;

    left.append(rank, nameEl);

    const countEl = document.createElement("div");
    countEl.className = "applicant-count";
    countEl.textContent = count;

    item.append(left, countEl);
    container.appendChild(item);
  });
}
