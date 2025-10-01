// Main JavaScript file for PH Control

// Global variables
let currentUser = null;
let notifications = [];

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

// Initialize application
function initializeApp() {
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize form validation
    initializeFormValidation();
    
    // Initialize file uploads
    initializeFileUploads();
    
    // Initialize notifications
    initializeNotifications();
    
    // Initialize charts if Chart.js is available
    if (typeof Chart !== 'undefined') {
        Chart.defaults.font.family = "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif";
        Chart.defaults.color = '#858796';
    }
    
    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach(function(alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
}

// Initialize Bootstrap tooltips
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Initialize form validation
function initializeFormValidation() {
    // Add Bootstrap validation classes
    const forms = document.querySelectorAll('.needs-validation');
    Array.prototype.slice.call(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
    
    // Custom validation for specific fields
    initializeCustomValidation();
}

// Initialize custom validation
function initializeCustomValidation() {
    // Email validation
    const emailInputs = document.querySelectorAll('input[type="email"]');
    emailInputs.forEach(function(input) {
        input.addEventListener('blur', function() {
            validateEmail(this);
        });
    });
    
    // Phone validation
    const phoneInputs = document.querySelectorAll('input[type="tel"]');
    phoneInputs.forEach(function(input) {
        input.addEventListener('blur', function() {
            validatePhone(this);
        });
    });
    
    // Password strength validation
    const passwordInputs = document.querySelectorAll('input[type="password"][name="password"], input[type="password"][name="new_password"]');
    passwordInputs.forEach(function(input) {
        input.addEventListener('input', function() {
            validatePasswordStrength(this);
        });
    });
}

// Validate email format
function validateEmail(input) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const isValid = emailRegex.test(input.value);
    
    if (input.value && !isValid) {
        input.setCustomValidity('Por favor ingresa un email válido');
        input.classList.add('is-invalid');
    } else {
        input.setCustomValidity('');
        input.classList.remove('is-invalid');
    }
}

// Validate phone format (Panama)
function validatePhone(input) {
    const phoneRegex = /^(\+507\s?)?[6-9]\d{3}-?\d{4}$/;
    const isValid = phoneRegex.test(input.value);
    
    if (input.value && !isValid) {
        input.setCustomValidity('Formato: +507 6000-0000 o 6000-0000');
        input.classList.add('is-invalid');
    } else {
        input.setCustomValidity('');
        input.classList.remove('is-invalid');
    }
}

// Validate password strength
function validatePasswordStrength(input) {
    const password = input.value;
    const strengthIndicator = document.getElementById('password-strength');
    
    if (!strengthIndicator) return;
    
    let strength = 0;
    let feedback = [];
    
    // Length check
    if (password.length >= 8) strength++;
    else feedback.push('Al menos 8 caracteres');
    
    // Uppercase check
    if (/[A-Z]/.test(password)) strength++;
    else feedback.push('Una letra mayúscula');
    
    // Lowercase check
    if (/[a-z]/.test(password)) strength++;
    else feedback.push('Una letra minúscula');
    
    // Number check
    if (/\d/.test(password)) strength++;
    else feedback.push('Un número');
    
    // Special character check
    if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) strength++;
    else feedback.push('Un carácter especial');
    
    // Update strength indicator
    const strengthClasses = ['text-danger', 'text-warning', 'text-info', 'text-success'];
    const strengthTexts = ['Muy débil', 'Débil', 'Regular', 'Fuerte', 'Muy fuerte'];
    
    strengthIndicator.className = `small ${strengthClasses[Math.min(strength - 1, 3)]}`;
    strengthIndicator.textContent = `Fortaleza: ${strengthTexts[strength]} ${feedback.length ? '(Falta: ' + feedback.join(', ') + ')' : ''}`;
}

// Initialize file uploads
function initializeFileUploads() {
    const uploadAreas = document.querySelectorAll('.upload-area');
    
    uploadAreas.forEach(function(area) {
        const fileInput = area.querySelector('input[type="file"]');
        
        if (!fileInput) return;
        
        // Drag and drop events
        area.addEventListener('dragover', function(e) {
            e.preventDefault();
            area.classList.add('dragover');
        });
        
        area.addEventListener('dragleave', function(e) {
            e.preventDefault();
            area.classList.remove('dragover');
        });
        
        area.addEventListener('drop', function(e) {
            e.preventDefault();
            area.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                fileInput.files = files;
                updateFileDisplay(area, files[0]);
            }
        });
        
        // Click to upload
        area.addEventListener('click', function() {
            fileInput.click();
        });
        
        // File input change
        fileInput.addEventListener('change', function() {
            if (this.files.length > 0) {
                updateFileDisplay(area, this.files[0]);
            }
        });
    });
}

// Update file display
function updateFileDisplay(area, file) {
    const fileName = area.querySelector('.file-name');
    const fileSize = area.querySelector('.file-size');
    
    if (fileName) {
        fileName.textContent = file.name;
    }
    
    if (fileSize) {
        fileSize.textContent = formatFileSize(file.size);
    }
    
    area.classList.add('has-file');
}

// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Initialize notifications
function initializeNotifications() {
    // Check for new notifications every 30 seconds
    setInterval(checkNotifications, 30000);
    
    // Mark notifications as read when clicked
    const notificationItems = document.querySelectorAll('.notification-item');
    notificationItems.forEach(function(item) {
        item.addEventListener('click', function() {
            const notificationId = this.dataset.notificationId;
            if (notificationId) {
                markNotificationAsRead(notificationId);
            }
        });
    });
}

// Check for new notifications
function checkNotifications() {
    fetch('/api/notifications/check')
        .then(response => response.json())
        .then(data => {
            if (data.new_notifications > 0) {
                updateNotificationBadge(data.new_notifications);
                showNotificationToast('Tienes nuevas notificaciones');
            }
        })
        .catch(error => console.error('Error checking notifications:', error));
}

// Update notification badge
function updateNotificationBadge(count) {
    const badge = document.querySelector('.notification-badge');
    if (badge) {
        badge.textContent = count;
        badge.style.display = count > 0 ? 'inline' : 'none';
    }
}

// Mark notification as read
function markNotificationAsRead(notificationId) {
    fetch(`/api/notifications/mark-read/${notificationId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const item = document.querySelector(`[data-notification-id="${notificationId}"]`);
            if (item) {
                item.classList.remove('unread');
            }
        }
    })
    .catch(error => console.error('Error marking notification as read:', error));
}

// Show notification toast
function showNotificationToast(message, type = 'info') {
    const toastContainer = document.getElementById('toast-container') || createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // Remove toast element after it's hidden
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}

// Create toast container if it doesn't exist
function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
    document.body.appendChild(container);
    return container;
}

// Utility functions
const Utils = {
    // Format currency
    formatCurrency: function(amount, currency = 'USD') {
        return new Intl.NumberFormat('es-PA', {
            style: 'currency',
            currency: currency
        }).format(amount);
    },
    
    // Format date
    formatDate: function(date, options = {}) {
        const defaultOptions = {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit'
        };
        return new Intl.DateTimeFormat('es-PA', {...defaultOptions, ...options}).format(new Date(date));
    },
    
    // Format datetime
    formatDateTime: function(datetime) {
        return new Intl.DateTimeFormat('es-PA', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        }).format(new Date(datetime));
    },
    
    // Debounce function
    debounce: function(func, wait, immediate) {
        let timeout;
        return function executedFunction() {
            const context = this;
            const args = arguments;
            const later = function() {
                timeout = null;
                if (!immediate) func.apply(context, args);
            };
            const callNow = immediate && !timeout;
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
            if (callNow) func.apply(context, args);
        };
    },
    
    // Show loading spinner
    showLoading: function() {
        const spinner = document.createElement('div');
        spinner.id = 'loading-spinner';
        spinner.className = 'spinner-overlay';
        spinner.innerHTML = `
            <div class="spinner-border spinner-border-custom text-primary" role="status">
                <span class="visually-hidden">Cargando...</span>
            </div>
        `;
        document.body.appendChild(spinner);
    },
    
    // Hide loading spinner
    hideLoading: function() {
        const spinner = document.getElementById('loading-spinner');
        if (spinner) {
            spinner.remove();
        }
    },
    
    // Confirm dialog
    confirm: function(message, callback) {
        if (confirm(message)) {
            callback();
        }
    },
    
    // Copy to clipboard
    copyToClipboard: function(text) {
        navigator.clipboard.writeText(text).then(function() {
            showNotificationToast('Copiado al portapapeles', 'success');
        }).catch(function(err) {
            console.error('Error copying to clipboard:', err);
            showNotificationToast('Error al copiar', 'danger');
        });
    }
};

// Export utilities to global scope
window.Utils = Utils;
window.showNotificationToast = showNotificationToast;

// Handle AJAX errors globally
document.addEventListener('ajaxError', function(event) {
    console.error('AJAX Error:', event.detail);
    showNotificationToast('Error en la comunicación con el servidor', 'danger');
});

// Handle form submissions with loading states
document.addEventListener('submit', function(event) {
    const form = event.target;
    if (form.classList.contains('ajax-form')) {
        event.preventDefault();
        handleAjaxForm(form);
    } else if (form.classList.contains('loading-form')) {
        Utils.showLoading();
    }
});

// Handle AJAX forms
function handleAjaxForm(form) {
    const formData = new FormData(form);
    const url = form.action || window.location.href;
    const method = form.method || 'POST';
    
    Utils.showLoading();
    
    fetch(url, {
        method: method,
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        Utils.hideLoading();
        
        if (data.success) {
            showNotificationToast(data.message || 'Operación exitosa', 'success');
            if (data.redirect) {
                window.location.href = data.redirect;
            }
        } else {
            showNotificationToast(data.message || 'Error en la operación', 'danger');
        }
    })
    .catch(error => {
        Utils.hideLoading();
        console.error('Error:', error);
        showNotificationToast('Error en la comunicación', 'danger');
    });
}

// Initialize search functionality
function initializeSearch() {
    const searchInputs = document.querySelectorAll('.search-input');
    
    searchInputs.forEach(function(input) {
        const debouncedSearch = Utils.debounce(function() {
            performSearch(input.value, input.dataset.searchUrl);
        }, 300);
        
        input.addEventListener('input', debouncedSearch);
    });
}

// Perform search
function performSearch(query, url) {
    if (query.length < 2) return;
    
    fetch(`${url}?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
            displaySearchResults(data);
        })
        .catch(error => console.error('Search error:', error));
}

// Display search results
function displaySearchResults(results) {
    const resultsContainer = document.getElementById('search-results');
    if (!resultsContainer) return;
    
    resultsContainer.innerHTML = '';
    
    if (results.length === 0) {
        resultsContainer.innerHTML = '<p class="text-muted">No se encontraron resultados</p>';
        return;
    }
    
    results.forEach(function(result) {
        const item = document.createElement('div');
        item.className = 'search-result-item';
        item.innerHTML = `
            <h6><a href="${result.url}">${result.title}</a></h6>
            <p class="text-muted">${result.description}</p>
        `;
        resultsContainer.appendChild(item);
    });
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeSearch);
} else {
    initializeSearch();
}