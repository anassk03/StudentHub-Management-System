
document.addEventListener('DOMContentLoaded', function () {

    // REPORTS ATTENDANCE PROGRESS BAR
    document.querySelectorAll('[data-percentage]').forEach(function (bar) {

        const percentage = Math.min(
            100,
            Math.max(0, Number(bar.dataset.percentage) || 0)
        );

        bar.style.width = percentage + '%';
    });

});
