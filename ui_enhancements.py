"""
UI/UX Enhancement utilities and components
"""
from flask import Blueprint, render_template, jsonify

ui_bp = Blueprint('ui', __name__)

# CSS animations and transitions
ANIMATION_STYLES = """
/* Enhanced UI Animations and Transitions */
:root {
    --primary-color: #3498db;
    --secondary-color: #2c3e50;
    --success-color: #27ae60;
    --warning-color: #f39c12;
    --danger-color: #e74c3c;
    --info-color: #17a2b8;
    --light-color: #f8f9fa;
    --dark-color: #343a40;
    --transition-speed: 0.3s;
    --hover-transform: translateY(-2px);
    --shadow-hover: 0 4px 8px rgba(0,0,0,0.15);
    --shadow-normal: 0 2px 4px rgba(0,0,0,0.1);
}

/* Smooth transitions for all interactive elements */
* {
    transition: all var(--transition-speed) ease;
}

/* Card hover effects */
.card {
    border: none;
    box-shadow: var(--shadow-normal);
    border-radius: 10px;
    overflow: hidden;
}

.card:hover {
    transform: var(--hover-transform);
    box-shadow: var(--shadow-hover);
}

.card-header {
    background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
    color: white;
    border-bottom: none;
    padding: 1rem 1.25rem;
}

/* Button animations */
.btn {
    border-radius: 25px;
    padding: 0.5rem 1.5rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    border: none;
    position: relative;
    overflow: hidden;
}

.btn::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
    transition: left 0.5s;
}

.btn:hover::before {
    left: 100%;
}

.btn:hover {
    transform: translateY(-1px);
    box-shadow: var(--shadow-hover);
}

/* Form input animations */
.form-control {
    border: 2px solid #e9ecef;
    border-radius: 8px;
    padding: 0.75rem 1rem;
    transition: all var(--transition-speed) ease;
}

.form-control:focus {
    border-color: var(--primary-color);
    box-shadow: 0 0 0 0.2rem rgba(52, 144, 220, 0.25);
    transform: scale(1.02);
}

/* Table row hover effects */
.table tbody tr {
    transition: all var(--transition-speed) ease;
}

.table tbody tr:hover {
    background-color: rgba(52, 144, 220, 0.1);
    transform: scale(1.01);
}

/* Modal animations */
.modal.fade .modal-dialog {
    transform: scale(0.8) translateY(-50px);
    transition: all var(--transition-speed) ease;
}

.modal.show .modal-dialog {
    transform: scale(1) translateY(0);
}

/* Loading spinner */
.spinner-border-custom {
    width: 3rem;
    height: 3rem;
    border: 0.25em solid rgba(52, 144, 220, 0.25);
    border-right-color: var(--primary-color);
    border-radius: 50%;
    animation: spinner-border 0.75s linear infinite;
}

/* Notification animations */
.notification-item {
    transform: translateX(100%);
    animation: slideInRight 0.5s ease forwards;
}

@keyframes slideInRight {
    to {
        transform: translateX(0);
    }
}

.notification-item.removing {
    animation: slideOutRight 0.5s ease forwards;
}

@keyframes slideOutRight {
    to {
        transform: translateX(100%);
        opacity: 0;
    }
}

/* Progress bar animations */
.progress-bar {
    transition: width 1s ease;
    background: linear-gradient(45deg, var(--primary-color), var(--success-color));
}

/* Sidebar animations */
.sidebar {
    transition: all var(--transition-speed) ease;
}

.sidebar.collapsed {
    margin-left: -250px;
}

/* Badge animations */
.badge {
    transition: all var(--transition-speed) ease;
}

.badge:hover {
    transform: scale(1.1);
}

/* Chart container animations */
.chart-container {
    opacity: 0;
    transform: translateY(20px);
    animation: fadeInUp 0.6s ease forwards;
}

@keyframes fadeInUp {
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* Status indicators */
.status-indicator {
    display: inline-block;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    animation: pulse 2s infinite;
}

.status-indicator.online {
    background-color: var(--success-color);
}

.status-indicator.offline {
    background-color: var(--danger-color);
}

.status-indicator.warning {
    background-color: var(--warning-color);
}

@keyframes pulse {
    0% {
        box-shadow: 0 0 0 0 rgba(52, 144, 220, 0.7);
    }
    70% {
        box-shadow: 0 0 0 10px rgba(52, 144, 220, 0);
    }
    100% {
        box-shadow: 0 0 0 0 rgba(52, 144, 220, 0);
    }
}

/* Dark mode styles */
.dark-mode {
    --primary-color: #4a90e2;
    --secondary-color: #2c3e50;
    --bg-color: #1a1a1a;
    --text-color: #e0e0e0;
    --card-bg: #2d2d2d;
}

.dark-mode body {
    background-color: var(--bg-color);
    color: var(--text-color);
}

.dark-mode .card {
    background-color: var(--card-bg);
    color: var(--text-color);
}

/* Responsive animations */
@media (max-width: 768px) {
    .card:hover {
        transform: none;
    }
    
    .btn:hover {
        transform: none;
    }
}

/* Loading overlay */
.loading-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 9999;
    opacity: 0;
    visibility: hidden;
    transition: all var(--transition-speed) ease;
}

.loading-overlay.show {
    opacity: 1;
    visibility: visible;
}

/* Success/Error message animations */
.alert {
    border: none;
    border-radius: 10px;
    animation: slideDown 0.5s ease;
}

@keyframes slideDown {
    from {
        transform: translateY(-100%);
        opacity: 0;
    }
    to {
        transform: translateY(0);
        opacity: 1;
    }
}

/* Floating action button */
.fab {
    position: fixed;
    bottom: 20px;
    right: 20px;
    width: 60px;
    height: 60px;
    border-radius: 50%;
    background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
    border: none;
    color: white;
    font-size: 24px;
    cursor: pointer;
    transition: all var(--transition-speed) ease;
    box-shadow: var(--shadow-normal);
    z-index: 1000;
}

.fab:hover {
    transform: scale(1.1) rotate(90deg);
    box-shadow: var(--shadow-hover);
}

/* Kanban board enhancements */
.kanban-column {
    background: var(--light-color);
    border-radius: 10px;
    padding: 1rem;
    margin: 0 0.5rem;
    min-height: 500px;
    box-shadow: var(--shadow-normal);
    transition: all var(--transition-speed) ease;
}

.kanban-column:hover {
    box-shadow: var(--shadow-hover);
}

.kanban-card {
    background: white;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 0.5rem;
    cursor: move;
    transition: all var(--transition-speed) ease;
    border-left: 4px solid var(--primary-color);
}

.kanban-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-hover);
}

.kanban-card.dragging {
    opacity: 0.5;
    transform: rotate(5deg);
}
"""

# JavaScript enhancements
ENHANCED_JS = """
// Enhanced UI JavaScript
class UIEnhancements {
    constructor() {
        this.initializeAnimations();
        this.initializeNotifications();
        this.initializeTheme();
        this.initializeLoadingStates();
    }

    initializeAnimations() {
        // Intersection Observer for scroll animations
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-in');
                }
            });
        }, observerOptions);

        // Observe all cards and charts
        document.querySelectorAll('.card, .chart-container').forEach(el => {
            observer.observe(el);
        });
    }

    initializeNotifications() {
        // Real-time notification system
        if (typeof io !== 'undefined') {
            const socket = io();
            
            socket.on('notification', (data) => {
                this.showNotification(data);
            });

            socket.on('connect', () => {
                console.log('Connected to notification server');
            });
        }
    }

    showNotification(data) {
        const notification = document.createElement('div');
        notification.className = `alert alert-${data.type} notification-item`;
        notification.innerHTML = `
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <strong>${data.title}</strong>
                    <p class="mb-0">${data.message}</p>
                </div>
                <button type="button" class="btn-close" aria-label="Close"></button>
            </div>
        `;

        const container = document.getElementById('notification-container') || this.createNotificationContainer();
        container.appendChild(notification);

        // Auto remove after 5 seconds
        setTimeout(() => {
            notification.classList.add('removing');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 500);
        }, 5000);

        // Manual close
        notification.querySelector('.btn-close').addEventListener('click', () => {
            notification.classList.add('removing');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 500);
        });
    }

    createNotificationContainer() {
        const container = document.createElement('div');
        container.id = 'notification-container';
        container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            width: 350px;
        `;
        document.body.appendChild(container);
        return container;
    }

    initializeTheme() {
        // Dark mode toggle
        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => {
                document.body.classList.toggle('dark-mode');
                const isDark = document.body.classList.contains('dark-mode');
                localStorage.setItem('theme', isDark ? 'dark' : 'light');
            });
        }

        // Load saved theme
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme === 'dark') {
            document.body.classList.add('dark-mode');
        }
    }

    initializeLoadingStates() {
        // Show loading overlay for AJAX requests
        let loadingCount = 0;
        const overlay = this.createLoadingOverlay();

        // Intercept fetch requests
        const originalFetch = window.fetch;
        window.fetch = function(...args) {
            loadingCount++;
            overlay.classList.add('show');
            
            return originalFetch.apply(this, args).finally(() => {
                loadingCount--;
                if (loadingCount === 0) {
                    overlay.classList.remove('show');
                }
            });
        };

        // Intercept form submissions
        document.addEventListener('submit', (e) => {
            if (e.target.classList.contains('ajax-form')) {
                e.preventDefault();
                this.handleAjaxForm(e.target);
            }
        });
    }

    createLoadingOverlay() {
        const overlay = document.createElement('div');
        overlay.className = 'loading-overlay';
        overlay.innerHTML = `
            <div class="spinner-border-custom" role="status">
                <span class="sr-only">Loading...</span>
            </div>
        `;
        document.body.appendChild(overlay);
        return overlay;
    }

    handleAjaxForm(form) {
        const formData = new FormData(form);
        const url = form.action || window.location.href;
        const method = form.method || 'POST';

        fetch(url, {
            method: method,
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.showNotification({
                    type: 'success',
                    title: 'Success',
                    message: data.message || 'Operation completed successfully'
                });
                if (data.redirect) {
                    window.location.href = data.redirect;
                }
            } else {
                this.showNotification({
                    type: 'danger',
                    title: 'Error',
                    message: data.message || 'An error occurred'
                });
            }
        })
        .catch(error => {
            this.showNotification({
                type: 'danger',
                title: 'Error',
                message: 'Network error occurred'
            });
        });
    }

    // Smooth scroll to element
    smoothScrollTo(element) {
        element.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
    }

    // Animate counter numbers
    animateCounter(element, target, duration = 1000) {
        let start = 0;
        const increment = target / (duration / 16);
        
        const timer = setInterval(() => {
            start += increment;
            element.textContent = Math.floor(start);
            
            if (start >= target) {
                element.textContent = target;
                clearInterval(timer);
            }
        }, 16);
    }

    // Initialize tooltips and popovers
    initializeTooltips() {
        // Bootstrap tooltips
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });

        // Bootstrap popovers
        const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
        popoverTriggerList.map(function (popoverTriggerEl) {
            return new bootstrap.Popover(popoverTriggerEl);
        });
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const ui = new UIEnhancements();
    ui.initializeTooltips();
});

// Export for use in other modules
window.UIEnhancements = UIEnhancements;
"""

@ui_bp.route('/styles.css')
def enhanced_styles():
    """Serve enhanced CSS styles"""
    from flask import Response
    return Response(ANIMATION_STYLES, mimetype='text/css')

@ui_bp.route('/enhancements.js')
def enhanced_javascript():
    """Serve enhanced JavaScript"""
    from flask import Response
    return Response(ENHANCED_JS, mimetype='application/javascript')

# Component templates
def render_enhanced_card(title, content, card_type="primary", actions=None):
    """Render enhanced card component"""
    return f"""
    <div class="card border-{card_type} mb-4">
        <div class="card-header bg-{card_type} text-white">
            <h5 class="card-title mb-0">{title}</h5>
        </div>
        <div class="card-body">
            {content}
        </div>
        {f'<div class="card-footer">{actions}</div>' if actions else ''}
    </div>
    """

def render_progress_bar(value, max_value=100, color="primary", animated=True):
    """Render animated progress bar"""
    percentage = (value / max_value) * 100
    animation_class = "progress-bar-striped progress-bar-animated" if animated else ""
    
    return f"""
    <div class="progress mb-3" style="height: 20px;">
        <div class="progress-bar bg-{color} {animation_class}" 
             role="progressbar" 
             style="width: {percentage}%"
             aria-valuenow="{value}" 
             aria-valuemin="0" 
             aria-valuemax="{max_value}">
            {value}/{max_value}
        </div>
    </div>
    """

def render_stat_card(title, value, icon, color="primary", trend=None):
    """Render statistics card with animation"""
    trend_html = ""
    if trend:
        trend_color = "success" if trend > 0 else "danger"
        trend_icon = "↗" if trend > 0 else "↘"
        trend_html = f'<small class="text-{trend_color}">{trend_icon} {abs(trend)}%</small>'
    
    return f"""
    <div class="col-md-3 mb-4">
        <div class="card bg-{color} text-white">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <h6 class="card-title">{title}</h6>
                        <h3 class="counter" data-target="{value}">0</h3>
                        {trend_html}
                    </div>
                    <div class="fs-2">
                        <i class="{icon}"></i>
                    </div>
                </div>
            </div>
        </div>
    </div>
    """

def render_notification_badge(count, color="danger"):
    """Render notification badge"""
    if count == 0:
        return ""
    
    return f"""
    <span class="badge bg-{color} rounded-pill">{count}</span>
    """

def render_status_indicator(status, label=""):
    """Render status indicator with pulse animation"""
    return f"""
    <span class="d-flex align-items-center">
        <span class="status-indicator {status} me-2"></span>
        {label}
    </span>
    """