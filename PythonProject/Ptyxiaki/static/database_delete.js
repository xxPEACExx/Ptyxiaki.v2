(function () {
  function $(id) { return document.getElementById(id); }
  function qsa(sel) { return Array.from(document.querySelectorAll(sel)); }

  let deleteMode = null;
  let undoTimer = null;
  let pendingDeletePayload = null;
  let hiddenRows = [];

  function getSelectedDidsOnPage() {
    return qsa(".rowDidCheckbox:checked")
      .map(cb => parseInt(cb.dataset.did, 10))
      .filter(Number.isFinite);
  }

  function updateDeleteButtonState() {
    const btn = $("deleteSelectedBtn");
    if (!btn) return;
    btn.disabled = !deleteMode;
    btn.classList.toggle("enabled", !!deleteMode);
  }

  function openModal(text) {
    $("deleteConfirmText").textContent = text;
    $("deleteConfirmModal").style.display = "flex";
  }

  function closeModal() {
    $("deleteConfirmModal").style.display = "none";
  }

  function showUndoToast(count) {
    removeUndoToast();

    const toast = document.createElement("div");
    toast.className = "undo-toast";
    toast.id = "undoToast";
    toast.innerHTML = `
      <span>Διαγράφηκαν ${count} εγγραφές</span>
      <button id="undoBtn">Undo</button>
    `;

    document.body.appendChild(toast);

    $("undoBtn").addEventListener("click", undoDelete);
  }

  function removeUndoToast() {
    $("undoToast")?.remove();
  }

  function hideRow(row) {
    row.classList.add("table-row-fadeout");
    setTimeout(() => {
      row.style.display = "none";
    }, 350);
  }

  function restoreRows() {
    hiddenRows.forEach(row => {
      row.style.display = "";
      requestAnimationFrame(() => {
        row.classList.remove("table-row-fadeout");
      });
    });
    hiddenRows = [];
  }

  async function commitDelete() {
    if (!pendingDeletePayload) return;

    try {
      await fetch("/api/documents/delete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(pendingDeletePayload)
      });

      if (window.invalidateSummaryCache) invalidateSummaryCache();
      if (window.fetchDatabaseSummary) fetchDatabaseSummary(true);

    } catch (e) {
      console.error("Delete failed", e);
    }

    pendingDeletePayload = null;
    removeUndoToast();
  }

  function undoDelete() {
    clearTimeout(undoTimer);
    restoreRows();
    pendingDeletePayload = null;
    removeUndoToast();
  }

  function prepareDelete() {
    let payload;

    if (deleteMode === "all") {
      payload = { mode: "all" };
      hiddenRows = qsa("tbody tr");
    } else if (deleteMode === "selected") {
      const dids = getSelectedDidsOnPage();
      if (!dids.length) return;
      payload = { mode: "selected", dids };
      hiddenRows = dids
        .map(did => document.querySelector(`tr[data-did="${did}"]`))
        .filter(Boolean);
    } else {
      return;
    }

    hiddenRows.forEach(hideRow);

    pendingDeletePayload = payload;
    showUndoToast(hiddenRows.length);

    undoTimer = setTimeout(commitDelete, 5000);

    closeModal();
    deleteMode = null;
    updateDeleteButtonState();
  }

  document.addEventListener("DOMContentLoaded", () => {
    const selectAll = $("selectAllDids");
    const deleteBtn = $("deleteSelectedBtn");

    if (!selectAll || !deleteBtn) return;

    selectAll.addEventListener("change", () => {
      if (selectAll.checked) {
        deleteMode = "all";
        qsa(".rowDidCheckbox").forEach(cb => cb.checked = true);
      } else {
        deleteMode = null;
        qsa(".rowDidCheckbox").forEach(cb => cb.checked = false);
      }
      updateDeleteButtonState();
    });

    qsa(".rowDidCheckbox").forEach(cb => {
      cb.addEventListener("change", () => {
        deleteMode = getSelectedDidsOnPage().length ? "selected" : null;
        selectAll.checked = false;
        updateDeleteButtonState();
      });
    });

    deleteBtn.addEventListener("click", () => {
      if (deleteMode === "all") {
        openModal("Θέλετε να διαγράψετε ΟΛΕΣ τις εγγραφές;");
      } else if (deleteMode === "selected") {
        openModal(`Θέλετε να διαγράψετε ${getSelectedDidsOnPage().length} εγγραφές;`);
      }
    });

    $("deleteCancelBtn")?.addEventListener("click", closeModal);
    $("deleteConfirmBtn")?.addEventListener("click", prepareDelete);

    updateDeleteButtonState();
  });
})();
