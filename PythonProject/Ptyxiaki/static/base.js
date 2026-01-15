document.addEventListener("DOMContentLoaded", async () => {
    const active = localStorage.getItem("upload_active");
    if (!active) return;

    try {
        const res = await fetch("/get_progress");
        const data = await res.json();

        if (data.status === "running" || data.status === "paused") {
            showUploadPopup();
            updateUploadProgress(data.progress ?? 0);
            startProcessingProgress(); // 🔁 ξαναπιάνει το interval
        } else {
            localStorage.removeItem("upload_active");
        }
    } catch (e) {
        console.error("Upload reconnect failed", e);
    }
});
