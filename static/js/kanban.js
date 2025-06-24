// Kanban Board Functionality for Nexus Flow

class KanbanBoard {
    constructor(projectId) {
        this.projectId = projectId;
        this.columns = ['todo', 'in_progress', 'done'];
        this.draggedTask = null;
        this.init();
    }

    init() {
        this.setupDragAndDrop();
        this.setupTaskCreation();
        this.setupTaskModals();
        this.setupAutoRefresh();
    }

    setupDragAndDrop() {
        const tasks = document.querySelectorAll('.task-card');
        const columns = document.querySelectorAll('.kanban-body');

        // Make tasks draggable
        tasks.forEach(task => {
            task.addEventListener('dragstart', (e) => {
                this.draggedTask = task;
                task.classList.add('dragging');
                e.dataTransfer.effectAllowed = 'move';
                e.dataTransfer.setData('text/html', task.outerHTML);
            });

            task.addEventListener('dragend', () => {
                task.classList.remove('dragging');
                this.draggedTask = null;
            });
        });

        // Setup drop zones
        columns.forEach(column => {
            column.addEventListener('dragover', (e) => {
                e.preventDefault();
                e.dataTransfer.dropEffect = 'move';
                column.classList.add('drag-over');
            });

            column.addEventListener('dragleave', () => {
                column.classList.remove('drag-over');
            });

            column.addEventListener('drop', (e) => {
                e.preventDefault();
                column.classList.remove('drag-over');
                
                if (this.draggedTask) {
                    const newStatus = column.getAttribute('data-status');
                    const taskId = this.draggedTask.getAttribute('data-task-id');
                    
                    // Calculate new position
                    const tasksInColumn = column.querySelectorAll('.task-card');
                    const newPosition = tasksInColumn.length;
                    
                    this.moveTask(taskId, newStatus, newPosition);
                }
            });
        });
    }

    moveTask(taskId, newStatus, newPosition) {
        const data = {
            status: newStatus,
            position: newPosition
        };

        fetch(`/flow/task/${taskId}/move`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                // Move the task in the DOM
                const targetColumn = document.querySelector(`[data-status="${newStatus}"] .kanban-body`);
                if (targetColumn && this.draggedTask) {
                    targetColumn.appendChild(this.draggedTask);
                    this.updateTaskCounts();
                    NexusApp.showToast('Task moved successfully', 'success');
                }
            } else {
                NexusApp.showToast('Failed to move task', 'danger');
                this.refreshBoard();
            }
        })
        .catch(error => {
            console.error('Error moving task:', error);
            NexusApp.showToast('Error moving task', 'danger');
            this.refreshBoard();
        });
    }

    setupTaskCreation() {
        const createButtons = document.querySelectorAll('.create-task-btn');
        
        createButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const status = button.getAttribute('data-status');
                this.showCreateTaskModal(status);
            });
        });

        // Quick task creation
        const quickForms = document.querySelectorAll('.quick-task-form');
        quickForms.forEach(form => {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                const formData = new FormData(form);
                this.createQuickTask(formData);
            });
        });
    }

    showCreateTaskModal(status = 'todo') {
        const modal = document.getElementById('createTaskModal');
        const statusSelect = modal.querySelector('#taskStatus');
        if (statusSelect) {
            statusSelect.value = status;
        }
        
        const bootstrapModal = new bootstrap.Modal(modal);
        bootstrapModal.show();
    }

    createQuickTask(formData) {
        const submitButton = document.querySelector('.quick-task-form button[type="submit"]');
        NexusApp.showLoading(submitButton);

        fetch('/flow/task/create', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                this.refreshBoard();
                NexusApp.showToast('Task created successfully', 'success');
                
                // Clear form
                const form = submitButton.closest('form');
                form.reset();
            } else {
                NexusApp.showToast('Failed to create task', 'danger');
            }
        })
        .catch(error => {
            console.error('Error creating task:', error);
            NexusApp.showToast('Error creating task', 'danger');
        })
        .finally(() => {
            NexusApp.hideLoading(submitButton);
        });
    }

    setupTaskModals() {
        const taskCards = document.querySelectorAll('.task-card');
        
        taskCards.forEach(card => {
            card.addEventListener('click', (e) => {
                // Don't trigger on drag
                if (e.target.closest('.task-actions')) return;
                
                const taskId = card.getAttribute('data-task-id');
                this.showTaskDetails(taskId);
            });
        });

        // Setup task detail modal form submission
        const taskDetailForm = document.getElementById('taskDetailForm');
        if (taskDetailForm) {
            taskDetailForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.saveTaskDetails();
            });
        }

        // Setup comment form
        const commentForm = document.getElementById('commentForm');
        if (commentForm) {
            commentForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.addComment();
            });
        }
    }

    showTaskDetails(taskId) {
        fetch(`/flow/api/task/${taskId}`)
        .then(response => response.json())
        .then(task => {
            this.populateTaskModal(task);
            const modal = new bootstrap.Modal(document.getElementById('taskDetailModal'));
            modal.show();
        })
        .catch(error => {
            console.error('Error loading task details:', error);
            NexusApp.showToast('Error loading task details', 'danger');
        });
    }

    populateTaskModal(task) {
        const modal = document.getElementById('taskDetailModal');
        
        modal.querySelector('#taskDetailId').value = task.id;
        modal.querySelector('#taskDetailTitle').value = task.title;
        modal.querySelector('#taskDetailDescription').value = task.description || '';
        modal.querySelector('#taskDetailPriority').value = task.priority;
        modal.querySelector('#taskDetailLabels').value = task.labels || '';
        
        const assignedSelect = modal.querySelector('#taskDetailAssigned');
        if (assignedSelect && task.assigned_to) {
            assignedSelect.value = task.assigned_to;
        }

        // Populate comments
        const commentsContainer = modal.querySelector('#taskComments');
        if (commentsContainer && task.comments) {
            commentsContainer.innerHTML = task.comments.map(comment => `
                <div class="comment mb-3">
                    <div class="d-flex justify-content-between">
                        <strong>${comment.user.name}</strong>
                        <small class="text-muted">${NexusApp.formatRelativeTime(comment.created_at)}</small>
                    </div>
                    <p class="mb-0 mt-1">${comment.content}</p>
                </div>
            `).join('');
        }

        // Update modal title
        modal.querySelector('.modal-title').textContent = `Task: ${task.title}`;
    }

    saveTaskDetails() {
        const form = document.getElementById('taskDetailForm');
        const formData = new FormData(form);
        const taskId = formData.get('task_id');
        
        const submitButton = form.querySelector('button[type="submit"]');
        NexusApp.showLoading(submitButton);

        fetch(`/flow/task/${taskId}/edit`, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                NexusApp.showToast('Task updated successfully', 'success');
                bootstrap.Modal.getInstance(document.getElementById('taskDetailModal')).hide();
                this.refreshBoard();
            } else {
                NexusApp.showToast('Failed to update task', 'danger');
            }
        })
        .catch(error => {
            console.error('Error updating task:', error);
            NexusApp.showToast('Error updating task', 'danger');
        })
        .finally(() => {
            NexusApp.hideLoading(submitButton);
        });
    }

    addComment() {
        const form = document.getElementById('commentForm');
        const formData = new FormData(form);
        const taskId = document.getElementById('taskDetailId').value;
        
        formData.append('task_id', taskId);
        
        const submitButton = form.querySelector('button[type="submit"]');
        NexusApp.showLoading(submitButton);

        fetch(`/flow/task/${taskId}/comment`, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                NexusApp.showToast('Comment added successfully', 'success');
                form.reset();
                
                // Refresh task details
                this.showTaskDetails(taskId);
            } else {
                NexusApp.showToast('Failed to add comment', 'danger');
            }
        })
        .catch(error => {
            console.error('Error adding comment:', error);
            NexusApp.showToast('Error adding comment', 'danger');
        })
        .finally(() => {
            NexusApp.hideLoading(submitButton);
        });
    }

    deleteTask(taskId) {
        if (!confirm('Are you sure you want to delete this task?')) {
            return;
        }

        fetch(`/flow/task/${taskId}/delete`, {
            method: 'POST'
        })
        .then(response => {
            if (response.ok) {
                NexusApp.showToast('Task deleted successfully', 'success');
                this.refreshBoard();
                
                // Close modal if open
                const modal = bootstrap.Modal.getInstance(document.getElementById('taskDetailModal'));
                if (modal) modal.hide();
            } else {
                NexusApp.showToast('Failed to delete task', 'danger');
            }
        })
        .catch(error => {
            console.error('Error deleting task:', error);
            NexusApp.showToast('Error deleting task', 'danger');
        });
    }

    updateTaskCounts() {
        this.columns.forEach(status => {
            const column = document.querySelector(`[data-status="${status}"]`);
            const tasks = column.querySelectorAll('.task-card');
            const counter = column.querySelector('.task-count');
            
            if (counter) {
                counter.textContent = tasks.length;
            }
        });
    }

    refreshBoard() {
        window.location.reload();
    }

    setupAutoRefresh() {
        // Auto-refresh every 30 seconds to sync with other users
        this.refreshInterval = setInterval(() => {
            this.refreshBoard();
        }, 30000);
    }

    destroy() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
    }
}

// Initialize Kanban board when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    const kanbanContainer = document.querySelector('.kanban-board');
    if (kanbanContainer) {
        const projectId = kanbanContainer.getAttribute('data-project-id');
        window.kanbanBoard = new KanbanBoard(projectId);
    }
});

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (window.kanbanBoard) {
        window.kanbanBoard.destroy();
    }
});
