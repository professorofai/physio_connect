// Custom JavaScript for Physio Connect - Interactive Frontend

// Wait for DOM to load
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Add fade-in animation to main content
    const mainContent = document.querySelector('.container');
    if (mainContent) {
        mainContent.classList.add('fade-in');
    }

    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Form validation enhancement
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();

                // Add visual feedback for invalid fields
                const invalidFields = form.querySelectorAll(':invalid');
                invalidFields.forEach(field => {
                    field.classList.add('is-invalid');
                    // Add shake animation
                    field.style.animation = 'shake 0.5s ease-in-out';
                    setTimeout(() => {
                        field.style.animation = '';
                    }, 500);
                });
            } else {
                // Show loading state for submit buttons
                const submitBtn = form.querySelector('button[type="submit"]');
                if (submitBtn) {
                    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...';
                    submitBtn.disabled = true;
                }
            }
            form.classList.add('was-validated');
        });

        // Real-time validation feedback
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                if (this.checkValidity()) {
                    this.classList.remove('is-invalid');
                    this.classList.add('is-valid');
                } else {
                    this.classList.remove('is-valid');
                    this.classList.add('is-invalid');
                }
            });
        });
    });

    // Image preview for file uploads (for profile pictures)
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file && file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    // Find or create preview element
                    let preview = input.parentNode.querySelector('.image-preview');
                    if (!preview) {
                        preview = document.createElement('img');
                        preview.className = 'image-preview mt-2 rounded';
                        preview.style.maxWidth = '200px';
                        preview.style.maxHeight = '200px';
                        input.parentNode.appendChild(preview);
                    }
                    preview.src = e.target.result;
                    preview.classList.add('slide-in-left');
                };
                reader.readAsDataURL(file);
            }
        });
    });

    // Dynamic navbar active state
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });

    // Add key shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + Enter to submit forms
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            const activeForm = document.activeElement.closest('form');
            if (activeForm) {
                const submitBtn = activeForm.querySelector('button[type="submit"]');
                if (submitBtn) {
                    submitBtn.click();
                }
            }
        }

        // Escape to close modals
        if (e.key === 'Escape') {
            const openModal = document.querySelector('.modal.show');
            if (openModal) {
                const bsModal = bootstrap.Modal.getInstance(openModal);
                if (bsModal) {
                    bsModal.hide();
                }
            }
        }
    });

    // Auto-dismiss flash messages after a short reading period.
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(flashMessage => {
        setTimeout(() => {
            flashMessage.classList.add('is-dismissing');
            setTimeout(() => flashMessage.remove(), 450);
        }, 4500);
    });

    // Add pulse animation to call-to-action buttons
    const ctaButtons = document.querySelectorAll('.btn-primary, .btn-success');
    ctaButtons.forEach(btn => {
        btn.addEventListener('mouseenter', function() {
            this.style.animation = 'pulse 1s infinite';
        });
        btn.addEventListener('mouseleave', function() {
            this.style.animation = '';
        });
    });

    // Initialize any Bootstrap components that need JS
    // (Bootstrap JS is already loaded above)
});

// Utility functions
function showToast(message, type = 'info') {
    const toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        const container = document.createElement('div');
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '1050';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;

    document.querySelector('.toast-container').appendChild(toast);
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();

    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

// Add shake animation keyframes via JS (fallback)
const firstStyleSheet = document.styleSheets[0];
let hasShakeAnimation = false;
try {
    hasShakeAnimation = firstStyleSheet && Array.from(firstStyleSheet.cssRules)
        .some(rule => rule.name === 'shake');
} catch (error) {
    hasShakeAnimation = false;
}

if (!hasShakeAnimation) {
    const style = document.createElement('style');
    style.textContent = `
        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            25% { transform: translateX(-5px); }
            75% { transform: translateX(5px); }
        }
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
    `;
    document.head.appendChild(style);
}