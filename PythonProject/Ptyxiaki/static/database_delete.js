let activeDelete = null;

const TOTAL_ROWS = parseInt(
  document.body.dataset.totalRows || "0",
  10
);


(function () {
  function $(id) {
    return document.getElementById(id);
  }

  function qsa(sel) {
    return Array.from(document.querySelectorAll(sel));
  }

  let deleteMode = null;

  // -------------------------
  // Helpers
  // -------------------------
  function getSelectedDidsOnPage() {
    return qsa(".rowDidCheckbox:checked")
      .map(cb => parseInt(cb.dataset.did, 10))
      .filter(Number.isFinite);
  }

  function updateDeleteButtonState() {
    const btn = $("deleteSelectedBtn");
    if (!btn) return;
    btn.disabled = !deleteMode || !!activeDelete;
    btn.classList.toggle("enabled", !!deleteMode && !activeDelete);
  }

  // -------------------------
  // Modal
  // -------------------------
  function openModal(text) {
    $("deleteConfirmText").textContent = text;
    $("deleteConfirmModal").style.display = "flex";
  }

  function closeModal() {
    $("deleteConfirmModal").style.display = "none";
  }

  // -------------------------
  // Undo Toast
  // -------------------------
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

  // -------------------------
  // UI row helpers
  // -------------------------
  function hideRow(row) {
    row.classList.add("table-row-fadeout");
    setTimeout(() => {
      row.style.display = "none";
    }, 300);
  }

  // -------------------------
  // Backend commit
  // -------------------------
  async function commitDelete(deleteAction) {
    if (!deleteAction) return;

    try {
      await fetch("/api/documents/delete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(deleteAction.payload)
      });

      if (window.invalidateSummaryCache) invalidateSummaryCache();
      if (window.fetchDatabaseSummary) fetchDatabaseSummary(true);

    } catch (e) {
      console.error("Delete failed", e);
    }

    removeUndoToast();
    deleteMode = null;
    updateDeleteButtonState();
  }

  // -------------------------
  // Undo (ΜΟΝΟ τελευταίο delete)
  // -------------------------
  function undoDelete() {
    if (!activeDelete) return;

    clearTimeout(activeDelete.timer);

    activeDelete.rows.forEach(row => {
      row.style.display = "";
      requestAnimationFrame(() => {
        row.classList.remove("table-row-fadeout");
      });
    });

    activeDelete = null;
    removeUndoToast();
    deleteMode = null;
    updateDeleteButtonState();
  }

  // -------------------------
  // Prepare Delete (CORE)
  // -------------------------
  function prepareDelete() {
    // ❌ ΜΗΝ επιτρέπεις νέο delete αν υπάρχει undo
    if (activeDelete) return;

    let payload;
    let rowsToHide = [];

    if (deleteMode === "all") {
      payload = { mode: "all" };
      rowsToHide = qsa("tbody tr").filter(row => row.style.display !== "none");

    } else if (deleteMode === "selected") {
      const dids = getSelectedDidsOnPage();
      if (!dids.length) return;

      payload = { mode: "selected", dids };
      rowsToHide = dids
        .map(did => document.querySelector(`tr[data-did="${did}"]`))
        .filter(Boolean);

    } else {
      return;
    }

    // UI hide
    rowsToHide.forEach(hideRow);

    // Καθάρισε checkboxes
    qsa(".rowDidCheckbox").forEach(cb => cb.checked = false);
    $("selectAllDids").checked = false;

    // Δέσε ΤΟ delete
    activeDelete = {
      payload,
      rows: rowsToHide,
      timer: null
    };

    const undoCount =
  deleteMode === "all"
    ? TOTAL_ROWS
    : rowsToHide.length;

showUndoToast(undoCount);


    // Commit μετά από 5s
    activeDelete.timer = setTimeout(() => {
      commitDelete(activeDelete);
      activeDelete = null;
    }, 5000);

    closeModal();
    deleteMode = null;
    updateDeleteButtonState();
  }

  // -------------------------
  // Events
  // -------------------------
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
        openModal(
          `Θέλετε να διαγράψετε ${getSelectedDidsOnPage().length} εγγραφές;`
        );
      }
    });

    $("deleteCancelBtn")?.addEventListener("click", closeModal);
    $("deleteConfirmBtn")?.addEventListener("click", prepareDelete);

    updateDeleteButtonState();
  });
})();
