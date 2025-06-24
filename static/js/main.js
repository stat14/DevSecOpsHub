// Nexus Platform Main JavaScript

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeTooltips();
    initializeAnimations();
    initializeFormValidation();
    initializeSearchFilters();
    initializeConfirmations();
    initializeClipboard();
});

// Initialize Bootstrap tooltips
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Initialize animations and transitions
function initializeAnimations() {
    // Fade in elements with fade-in class
    const fadeElements = document.querySelectorAll('.fade-in');
    fadeElements.forEach((element, index) => {
        element.style.opacity = '0';
        element.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            element.style.transition = 'all 0.5s ease-out';
            element.style.opacity = '1';
            element.style.transform = 'translateY(0)';
        }, index * 100);
    });

    // Hover effects for cards
    const cards = document.querySelectorAll('.card, .dashboard-card');
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transition = 'all 0.3s ease';
            this.style.transform = 'translateY(-2px)';
        });

        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
}

// Form validation
function initializeFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
                
                // Show first invalid field
                const firstInvalidField = form.querySelector(':invalid');
                if (firstInvalidField) {
                    firstInvalidField.focus();
                    showToast('Please fill in all required fields correctly.', 'warning');
                }
            }
            
            form.classList.add('was-validated');
        });

        // Real-time validation
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

    // Password strength indicator
    const passwordFields = document.querySelectorAll('input[type="password"]');
    passwordFields.forEach(field => {
        field.addEventListener('input', function() {
            const strength = getPasswordStrength(this.value);
            showPasswordStrength(this, strength);
        });
    });
}

// Password strength checker
function getPasswordStrength(password) {
    let score = 0;
    const checks = {
        length: password.length >= 8,
        lowercase: /[a-z]/.test(password),
        uppercase: /[A-Z]/.test(password),
        numbers: /\d/.test(password),
        symbols: /[^A-Za-z0-9]/.test(password)
    };

    Object.values(checks).forEach(check => {
        if (check) score++;
    });

    if (score < 2) return { level: 'weak', color: '#dc2626' };
    if (score < 4) return { level: 'medium', color: '#d97706' };
    return { level: 'strong', color: '#059669' };
}

// Show password strength indicator
function showPasswordStrength(field, strength) {
    let indicator = field.parentNode.querySelector('.password-strength');
    
    if (!indicator) {
        indicator = document.createElement('div');
        indicator.className = 'password-strength mt-1';
        field.parentNode.appendChild(indicator);
    }

    indicator.innerHTML = `
        <div class="progress" style="height: 4px;">
            <div class="progress-bar" style="width: ${strength.level === 'weak' ? '33%' : strength.level === 'medium' ? '66%' : '100%'}; background-color: ${strength.color};"></div>
        </div>
        <small class="text-muted">Password strength: <span style="color: ${strength.color};">${strength.level}</span></small>
    `;
}

// Search and filter functionality
function initializeSearchFilters() {
    const searchInputs = document.querySelectorAll('[data-search]');
    
    searchInputs.forEach(input => {
        const targetSelector = input.getAttribute('data-search');
        const targets = document.querySelectorAll(targetSelector);
        
        input.addEventListener('input', function() {
            const query = this.value.toLowerCase().trim();
            
            targets.forEach(target => {
                const text = target.textContent.toLowerCase();
                const shouldShow = text.includes(query);
                
                target.style.display = shouldShow ? '' : 'none';
                
                // Add highlight
                if (shouldShow && query) {
                    highlightText(target, query);
                } else {
                    removeHighlight(target);
                }
            });
        });
    });

    // Filter dropdowns
    const filterSelects = document.querySelectorAll('[data-filter]');
    
    filterSelects.forEach(select => {
        select.addEventListener('change', function() {
            const filterType = this.getAttribute('data-filter');
            const filterValue = this.value;
            const targets = document.querySelectorAll(`[data-${filterType}]`);
            
            targets.forEach(target => {
                const targetValue = target.getAttribute(`data-${filterType}`);
                const shouldShow = !filterValue || targetValue === filterValue;
                target.style.display = shouldShow ? '' : 'none';
            });
        });
    });
}

// Highlight search text
function highlightText(element, query) {
    removeHighlight(element);
    
    const walker = document.createTreeWalker(
        element,
        NodeFilter.SHOW_TEXT,
        null,
        false
    );

    const textNodes = [];
    let node;
    
    while (node = walker.nextNode()) {
        textNodes.push(node);
    }

    textNodes.forEach(textNode => {
        const text = textNode.textContent;
        const index = text.toLowerCase().indexOf(query);
        
        if (index !== -1) {
            const highlightedText = text.substring(0, index) +
                '<mark class="bg-warning">' +
                text.substring(index, index + query.length) +
                '</mark>' +
                text.substring(index + query.length);
            
            const wrapper = document.createElement('span');
            wrapper.innerHTML = highlightedText;
            textNode.parentNode.replaceChild(wrapper, textNode);
        }
    });
}

// Remove highlight
function removeHighlight(element) {
    const marks = element.querySelectorAll('mark');
    marks.forEach(mark => {
        mark.replaceWith(mark.textContent);
    });
}

// Confirmation dialogs
function initializeConfirmations() {
    const confirmButtons = document.querySelectorAll('[data-confirm]');
    
    confirmButtons.forEach(button => {
        button.addEventListener('click', function(event) {
            const message = this.getAttribute('data-confirm');
            
            if (!confirm(message)) {
                event.preventDefault();
                return false;
            }
        });
    });
}

// Clipboard functionality
function initializeClipboard() {
    const copyButtons = document.querySelectorAll('[data-copy]');
    
    copyButtons.forEach(button => {
        button.addEventListener('click', function() {
            const text = this.getAttribute('data-copy');
            
            navigator.clipboard.writeText(text).then(() => {
                showToast('Copied to clipboard!', 'success');
                
                // Visual feedback
                const originalText = this.innerHTML;
                this.innerHTML = '<i class="fas fa-check"></i> Copied!';
                
                setTimeout(() => {
                    this.innerHTML = originalText;
                }, 2000);
            }).catch(() => {
                showToast('Failed to copy to clipboard', 'danger');
            });
        });
    });
}

// Toast notifications
function showToast(message, type = 'info') {
    // Remove existing toasts
    const existingToasts = document.querySelectorAll('.toast-notification');
    existingToasts.forEach(toast => toast.remove());

    const toast = document.createElement('div');
    toast.className = `alert alert-${type} toast-notification position-fixed`;
    toast.style.cssText = `
        top: 20px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
        animation: slideInRight 0.3s ease-out;
    `;
    
    toast.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="fas fa-${getToastIcon(type)} me-2"></i>
            ${message}
            <button type="button" class="btn-close ms-auto" onclick="this.parentElement.parentElement.remove()"></button>
        </div>
    `;

    document.body.appendChild(toast);

    // Auto remove after 5 seconds
    setTimeout(() => {
        if (toast.parentNode) {
            toast.style.animation = 'slideOutRight 0.3s ease-out';
            setTimeout(() => toast.remove(), 300);
        }
    }, 5000);
}

// Get icon for toast type
function getToastIcon(type) {
    const icons = {
        success: 'check-circle',
        danger: 'exclamation-circle',
        warning: 'exclamation-triangle',
        info: 'info-circle'
    };
    return icons[type] || 'info-circle';
}

// Loading states
function showLoading(element) {
    element.disabled = true;
    element.classList.add('loading');
    
    const originalText = element.innerHTML;
    element.setAttribute('data-original-text', originalText);
    element.innerHTML = '<span class="spinner me-2"></span>Loading...';
}

function hideLoading(element) {
    element.disabled = false;
    element.classList.remove('loading');
    
    const originalText = element.getAttribute('data-original-text');
    if (originalText) {
        element.innerHTML = originalText;
        element.removeAttribute('data-original-text');
    }
}

// AJAX helpers
function makeRequest(url, options = {}) {
    const defaultOptions = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
    };

    const config = { ...defaultOptions, ...options };

    return fetch(url, config)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .catch(error => {
            console.error('Request failed:', error);
            showToast('Request failed. Please try again.', 'danger');
            throw error;
        });
}

// Auto-refresh functionality
function startAutoRefresh(callback, interval = 30000) {
    return setInterval(callback, interval);
}

function stopAutoRefresh(intervalId) {
    if (intervalId) {
        clearInterval(intervalId);
    }
}

// Utility functions
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatRelativeTime(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffMinutes = Math.floor(diffMs / (1000 * 60));

    if (diffDays > 0) {
        return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    } else if (diffHours > 0) {
        return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    } else if (diffMinutes > 0) {
        return `${diffMinutes} minute${diffMinutes > 1 ? 's' : ''} ago`;
    } else {
        return 'Just now';
    }
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideOutRight {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);

// Global error handler
window.addEventListener('error', function(event) {
    console.error('Global error:', event.error);
    showToast('An unexpected error occurred', 'danger');
});

// Export functions for use in other scripts
window.NexusApp = {
    showToast,
    showLoading,
    hideLoading,
    makeRequest,
    formatDate,
    formatRelativeTime,
    debounce,
    startAutoRefresh,
    stopAutoRefresh
};
