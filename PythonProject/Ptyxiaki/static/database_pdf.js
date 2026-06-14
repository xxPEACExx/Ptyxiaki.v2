document.addEventListener("DOMContentLoaded", () => {
  const pdfBtn = document.getElementById("downloadPdfBtn");
  const selectAll = document.getElementById("selectAllDids");

  pdfBtn.disabled = false;
  pdfBtn.style.cursor = "pointer";
  pdfBtn.style.opacity = "1";

  function getSelectedDids() {
    return [...document.querySelectorAll(".rowDidCheckbox:checked")]
      .map(cb => cb.dataset.did || cb.value)
      .filter(Boolean);
  }

  pdfBtn.addEventListener("click", (e) => {
    e.preventDefault();

    if (selectAll && selectAll.checked) {
      window.location.href = "/download_all_documents_pdf";
      return;
    }

    const dids = getSelectedDids();

    if (dids.length === 0) {
      alert("Επίλεξε πρώτα εγγραφές.");
      return;
    }

    window.location.href =
      `/download_documents_pdf?dids=${encodeURIComponent(dids.join(","))}`;
  });
});