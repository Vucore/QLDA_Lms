document.addEventListener('DOMContentLoaded', function () {
    // Prevent default Bootstrap alert behavior
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        // Remove Bootstrap's auto-dismiss behavior
        alert.removeAttribute('data-bs-dismiss');

        // Add custom close button behavior
        const closeButton = alert.querySelector('.btn-close');
        if (closeButton) {
            closeButton.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                const parentAlert = e.target.closest('.alert');
                if (parentAlert) {
                    parentAlert.classList.remove('show');
                    parentAlert.classList.add('hide');
                    setTimeout(() => {
                        parentAlert.remove();
                    }, 150); // Match Bootstrap's transition timing
                }
            });
        }
    });
});
