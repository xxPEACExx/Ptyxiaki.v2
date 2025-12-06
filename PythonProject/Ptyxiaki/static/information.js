document.addEventListener("DOMContentLoaded", function () {
    // MAIN AREA CHART (Hero)
    const mainOptions = {
      chart: {
        type: "area",
        height: 260,
        toolbar: { show: false },
        zoom: { enabled: false },
      },
      series: [
        {
          name: "Πρόοδος δειγμάτων",
          data: [12, 21, 30, 38, 44, 52, 60, 68, 76, 82, 89, 92],
        },
        {
          name: "Ποιότητα δεδομένων",
          data: [70, 73, 75, 77, 79, 81, 83, 85, 87, 88, 90, 91],
        },
      ],
      stroke: {
        curve: "smooth",
        width: 3,
      },
      dataLabels: { enabled: false },
      legend: {
        show: true,
        position: "top",
        horizontalAlign: "left",
      },
      xaxis: {
        categories: [
          "Εβδ.1",
          "Εβδ.2",
          "Εβδ.3",
          "Εβδ.4",
          "Εβδ.5",
          "Εβδ.6",
          "Εβδ.7",
          "Εβδ.8",
          "Εβδ.9",
          "Εβδ.10",
          "Εβδ.11",
          "Εβδ.12",
        ],
        labels: { style: { fontSize: "11px" } },
        axisBorder: { show: false },
      },
      yaxis: {
        labels: { style: { fontSize: "11px" } },
        min: 0,
        max: 100,
      },
      grid: {
        borderColor: "#e5e7eb",
        strokeDashArray: 4,
      },
      colors: ["#fb923c", "#6366f1"],
      fill: {
        type: "gradient",
        gradient: {
          shadeIntensity: 0.9,
          opacityFrom: 0.3,
          opacityTo: 0.02,
          stops: [0, 80, 100],
        },
      },
      tooltip: {
        theme: "light",
      },
    };

    const mainChart = new ApexCharts(
      document.querySelector("#chart-main"),
      mainOptions
    );
    mainChart.render();

    // BAR CHART (Stats)
    const barOptions = {
      chart: {
        type: "bar",
        height: 190,
        toolbar: { show: false },
      },
      series: [
        {
          name: "Καταγεγραμμένα δεδομένα",
          data: [1800, 2300, 2900, 3100, 3500, 4100],
        },
      ],
      xaxis: {
        categories: ["Ιαν", "Φεβ", "Μαρ", "Απρ", "Μαι", "Ιουν"],
        labels: { style: { fontSize: "10px" } },
        axisBorder: { show: false },
        axisTicks: { show: false },
      },
      plotOptions: {
        bar: {
          borderRadius: 6,
          columnWidth: "42%",
        },
      },
      yaxis: {
        labels: { style: { fontSize: "10px" } },
      },
      grid: {
        borderColor: "#e5e7eb",
        strokeDashArray: 4,
      },
      colors: ["#111827"],
      dataLabels: { enabled: false },
      tooltip: {
        theme: "light",
      },
    };

    const barChart = new ApexCharts(
      document.querySelector("#chart-bar"),
      barOptions
    );
    barChart.render();

    // RADIAL BAR (Features completion)
    const radialOptions = {
      chart: {
        type: "radialBar",
        height: 230,
      },
      series: [95, 88, 92, 86],
      labels: [
        "Συλλογή",
        "Ανάλυση",
        "Οπτικοποίηση",
        "Αναφορές",
      ],
      plotOptions: {
        radialBar: {
          hollow: {
            size: "34%",
          },
          dataLabels: {
            name: {
              fontSize: "10px",
            },
            value: {
              fontSize: "14px",
              formatter: function (val) {
                return val + "%";
              },
            },
            total: {
              show: true,
              label: "Μέση ολοκλήρωση",
              fontSize: "10px",
              formatter: function (w) {
                const values = w.globals.seriesTotals;
                const total =
                  values.reduce((a, b) => a + b, 0) / values.length;
                return total.toFixed(1) + "%";
              },
            },
          },
        },
      },
      colors: ["#fb923c", "#6366f1", "#10b981", "#0ea5e9"],
      legend: {
        show: false,
      },
    };

    const radialChart = new ApexCharts(
      document.querySelector("#chart-radial"),
      radialOptions
    );
    radialChart.render();
  });