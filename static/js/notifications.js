// Real-time notifications system
class NotificationManager {
    constructor() {
        this.socket = null;
        this.container = null;
        this.initializeSocket();
        this.createContainer();
    }

    initializeSocket() {
        if (typeof io !== 'undefined') {
            this.socket = io();
            
            this.socket.on('connect', () => {
                console.log('Connected to notification server');
            });

            this.socket.on('notification', (data) => {
                this.showNotification(data);
            });

            this.socket.on('disconnect', () => {
                console.log('Disconnected from notification server');
            });
        }
    }

    createContainer() {
        this.container = document.createElement('div');
        this.container.id = 'notification-container';
        this.container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            width: 350px;
            max-height: 80vh;
            overflow-y: auto;
        `;
        document.body.appendChild(this.container);
    }

    showNotification(data) {
        const notification = document.createElement('div');
        notification.className = `alert alert-${data.type} notification-item`;
        notification.innerHTML = `
            <div class="d-flex justify-content-between align-items-start">
                <div class="flex-grow-1">
                    <h6 class="alert-heading mb-1">${data.title}</h6>
                    <p class="mb-1">${data.message}</p>
                    <small class="text-muted">${new Date(data.timestamp).toLocaleString()}</small>
                </div>
                <button type="button" class="btn-close" aria-label="Close"></button>
            </div>
        `;

        this.container.appendChild(notification);

        // Auto remove after 10 seconds for info/success, 15 seconds for warnings/errors
        const autoRemoveTime = (data.type === 'danger' || data.type === 'warning') ? 15000 : 10000;
        setTimeout(() => {
            this.removeNotification(notification);
        }, autoRemoveTime);

        // Manual close
        notification.querySelector('.btn-close').addEventListener('click', () => {
            this.removeNotification(notification);
        });

        // Mark as read when clicked
        notification.addEventListener('click', () => {
            if (this.socket && data.id) {
                this.socket.emit('mark_read', { notification_id: data.id });
            }
        });

        // Limit to 5 notifications max
        while (this.container.children.length > 5) {
            this.removeNotification(this.container.firstChild);
        }
    }

    removeNotification(notification) {
        if (notification && notification.parentNode) {
            notification.classList.add('removing');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 500);
        }
    }

    // Manual notification for local use
    notify(title, message, type = 'info') {
        this.showNotification({
            id: Date.now().toString(),
            title: title,
            message: message,
            type: type,
            timestamp: new Date().toISOString()
        });
    }
}

// Initialize notification manager when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.notificationManager = new NotificationManager();
});

// Utility function for easy access
function notify(title, message, type = 'info') {
    if (window.notificationManager) {
        window.notificationManager.notify(title, message, type);
    }
}