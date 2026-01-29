

document.addEventListener("DOMContentLoaded", () => {
  fetch("/api/overview")
    .then(res => res.json())
    .then(data => {
      // Αριθμητικά cards
      document.getElementById("total-docs").textContent = data.total_documents;
      document.getElementById("unique-applicants").textContent = data.unique_applicants;
      document.getElementById("max-claims").textContent = data.max_claims;
      document.getElementById("languages-count").textContent = data.languages_count;
      document.getElementById("docs-with-description").textContent = data.documents_with_description;
      document.getElementById("multi-lang-titles").textContent = data.multilingual_titles;

      // Εύρος ημερομηνιών
      if (data.date_range.min && data.date_range.max) {
        document.getElementById("date-range").textContent =
          `${data.date_range.min} — ${data.date_range.max}`;
      }

      // Χώρες → donut
      renderCountriesDonut(data.countries);
    });
});


function renderCountriesDonut(countries) {
  const ctx = document.getElementById("countriesChart").getContext("2d");

  const labels = Object.keys(countries);
  const values = Object.values(countries);

  new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: labels,
      datasets: [{
        data: values,
        backgroundColor: ["#3b82f6", "#22c55e", "#f59e0b", "#ef4444"]
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: {
          display: false
        }
      },
      cutout: "65%"
    }
  });

  // Legend text (EP – 100 κτλ)
  const legend = document.getElementById("countriesLegend");
  legend.innerHTML = labels
    .map((l, i) => `${l} – ${values[i]}`)
    .join(" | ");
}
