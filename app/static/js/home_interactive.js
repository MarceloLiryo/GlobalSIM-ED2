(function () {
    const stepper = document.querySelector("[data-how-stepper]");
    if (!stepper) return;

    const slides = Array.from(stepper.querySelectorAll("[data-step-slide]"));
    const dots = Array.from(stepper.querySelectorAll("[data-step-dot]"));
    const prevBtn = stepper.querySelector("[data-step-prev]");
    const nextBtn = stepper.querySelector("[data-step-next]");
    const progressBar = stepper.querySelector("[data-step-progress]");
    if (slides.length === 0) return;

    const INTERVAL_MS = 4000;
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let current = 0;
    let timerId = null;

    function restartProgress() {
        if (!progressBar || reducedMotion) return;
        progressBar.classList.remove("is-running");
        void progressBar.offsetWidth;
        progressBar.classList.add("is-running");
    }

    function showStep(index) {
        current = (index + slides.length) % slides.length;
        slides.forEach((slide, i) => {
            const active = i === current;
            slide.classList.toggle("is-active", active);
            slide.hidden = !active;
        });
        dots.forEach((dot, i) => {
            const active = i === current;
            dot.classList.toggle("is-active", active);
            dot.setAttribute("aria-selected", active ? "true" : "false");
        });
        restartProgress();
    }

    function startAutoplay() {
        if (reducedMotion) return;
        stopAutoplay();
        restartProgress();
        timerId = window.setInterval(() => showStep(current + 1), INTERVAL_MS);
    }

    function stopAutoplay() {
        if (timerId !== null) {
            window.clearInterval(timerId);
            timerId = null;
        }
        if (progressBar) {
            progressBar.classList.remove("is-running");
        }
    }

    prevBtn?.addEventListener("click", () => {
        showStep(current - 1);
        startAutoplay();
    });

    nextBtn?.addEventListener("click", () => {
        showStep(current + 1);
        startAutoplay();
    });

    dots.forEach((dot, i) => {
        dot.addEventListener("click", () => {
            showStep(i);
            startAutoplay();
        });
    });

    stepper.addEventListener("mouseenter", stopAutoplay);
    stepper.addEventListener("mouseleave", startAutoplay);
    stepper.addEventListener("focusin", stopAutoplay);
    stepper.addEventListener("focusout", startAutoplay);

    showStep(0);
    startAutoplay();
})();
