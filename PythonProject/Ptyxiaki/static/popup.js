window.onload = function () {
    const popup = document.getElementById("modernPopup");
    const circle = document.getElementById("floatingCircle");
    const bar = popup.querySelector(".progress-bar");

    const duration = 8000; // ms

    // Show popup
    setTimeout(() => {
        popup.classList.add("show");
        bar.style.transitionDuration = duration + "ms";
        bar.style.width = "100%";
    }, 200);

    // Hide popup → show circle
    setTimeout(() => {
        popup.classList.remove("show");

        setTimeout(() => {
            popup.style.display = "none";
            circle.style.display = "flex";
        }, 500);
    }, duration + 250);

    // Click actions
    popup.onclick = () => window.location.href = "/information";
    circle.onclick = () => window.location.href = "/information";
};
