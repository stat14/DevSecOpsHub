// Findings Management for Nexus Secure

class FindingsManager {
    constructor(projectId) {
        this.projectId = projectId;
        this.currentFilters = {
            severity: '',
            status: '',
            sort: 'created_at'
        };
        this.init();
    }

    init() {
        this.setupFilters();
        this.setupFindingModals();
        this.setupSearch();
        this.setupPagination();
        this.initializeRichTextEditor();
    }

    setupFilters() {
        const filterForm = document.getElementById('findingFilters');
        if (!filterForm) return;

        const severityFilter = filterForm.querySelector('#severityFilter');
        const statusFilter = filterForm.querySelector('#statusFilter');
        const sortFilter = filterForm.querySelector('#sortFilter');

        [severityFilter, statusFilter, sortFilter].forEach(filter => {
            if (filter) {
                filter.addEventListener('change', () => {
                    this.applyFilters();
                });
            }
        });

        // Clear filters button
        const clearFiltersBtn = document.getElementById('clearFilters');
        if (clearFiltersBtn) {
            clearFiltersBtn.addEventListener('click', () => {
                this.clearFilters();
            });
        }
    }

    applyFilters() {
        const form = document.getElementById('findingFilters');
        const formData = new FormData(form);
        
        this.currentFilters = {
            severity: formData.get('severity') || '',
            status: formData.get('status') || '',
            sort: formData.get('sort') || 'created_at'
        };

        // Update URL parameters
        const url = new URL(window.location);
        Object.keys(this.currentFilters).forEach(key => {
            if (this.currentFilters[key]) {
                url.searchParams.set(key, this.currentFilters[key]);
            } else {
                url.searchParams.delete(key);
            }
        });

        window.history.pushState({}, '', url);
        this.filterFindings();
    }

    filterFindings() {
        const findings = document.querySelectorAll('.finding-item');
        let visibleCount = 0;

        findings.forEach(finding => {
            const severity = finding.getAttribute('data-severity');
            const status = finding.getAttribute('data-status');
            
            let shouldShow = true;

            if (this.currentFilters.severity && severity !== this.currentFilters.severity) {
                shouldShow = false;
            }

            if (this.currentFilters.status && status !== this.currentFilters.status) {
                shouldShow = false;
            }

            finding.style.display = shouldShow ? '' : 'none';
            if (shouldShow) visibleCount++;
        });

        // Update results count
        const resultsCount = document.getElementById('resultsCount');
        if (resultsCount) {
            resultsCount.textContent = `${visibleCount} finding${visibleCount !== 1 ? 's' : ''}`;
        }

        // Sort visible findings if needed
        if (this.currentFilters.sort !== 'created_at') {
            this.sortFindings();
        }
    }

    sortFindings() {
        const container = document.querySelector('.findings-list');
        if (!container) return;

        const findings = Array.from(container.querySelectorAll('.finding-item'));
        const visibleFindings = findings.filter(f => f.style.display !== 'none');

        if (this.currentFilters.sort === 'severity') {
            const severityOrder = { 'critical': 0, 'high': 1, 'medium': 2, 'low': 3, 'informational': 4 };
            
            visibleFindings.sort((a, b) => {
                const aSeverity = a.getAttribute('data-severity');
                const bSeverity = b.getAttribute('data-severity');
                return severityOrder[aSeverity] - severityOrder[bSeverity];
            });
        }

        // Reorder in DOM
        visibleFindings.forEach(finding => {
            container.appendChild(finding);
        });
    }

    clearFilters() {
        const form = document.getElementById('findingFilters');
        if (form) {
            form.reset();
            this.currentFilters = { severity: '', status: '', sort: 'created_at' };
            
            // Clear URL parameters
            const url = new URL(window.location);
            ['severity', 'status', 'sort'].forEach(param => {
                url.searchParams.delete(param);
            });
            window.history.pushState({}, '', url);
            
            this.filterFindings();
        }
    }

    setupFindingModals() {
        // Create finding modal
        const createFindingBtn = document.getElementById('createFindingBtn');
        if (createFindingBtn) {
            createFindingBtn.addEventListener('click', () => {
                this.showCreateFindingModal();
            });
        }

        // Finding detail modals
        const findingCards = document.querySelectorAll('.finding-item');
        findingCards.forEach(card => {
            card.addEventListener('click', (e) => {
                if (e.target.closest('.finding-actions')) return;
                
                const findingId = card.getAttribute('data-finding-id');
                this.showFindingDetails(findingId);
            });
        });

        // Setup form submissions
        const createForm = document.getElementById('createFindingForm');
        if (createForm) {
            createForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.createFinding();
            });
        }

        const editForm = document.getElementById('editFindingForm');
        if (editForm) {
            editForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.saveFindingDetails();
            });
        }
    }

    showCreateFindingModal() {
        const modal = document.getElementById('createFindingModal');
        const bootstrapModal = new bootstrap.Modal(modal);
        bootstrapModal.show();
    }

    showFindingDetails(findingId) {
        fetch(`/secure/api/finding/${findingId}`)
        .then(response => response.json())
        .then(finding => {
            this.populateFindingModal(finding);
            const modal = new bootstrap.Modal(document.getElementById('findingDetailModal'));
            modal.show();
        })
        .catch(error => {
            console.error('Error loading finding details:', error);
            NexusApp.showToast('Error loading finding details', 'danger');
        });
    }

    populateFindingModal(finding) {
        const modal = document.getElementById('findingDetailModal');
        
        modal.querySelector('#findingDetailId').value = finding.id;
        modal.querySelector('#findingDetailTitle').value = finding.title;
        modal.querySelector('#findingDetailSeverity').value = finding.severity;
        modal.querySelector('#findingDetailStatus').value = finding.status;
        modal.querySelector('#findingDetailCvssScore').value = finding.cvss_score || '';
        modal.querySelector('#findingDetailCweId').value = finding.cwe_id || '';
        modal.querySelector('#findingDetailAffectedUrl').value = finding.affected_url || '';

        // Set rich text content
        if (window.findingDescriptionEditor) {
            window.findingDescriptionEditor.setContent(finding.description || '');
        }
        if (window.findingRemediationEditor) {
            window.findingRemediationEditor.setContent(finding.remediation || '');
        }

        // Update modal title
        modal.querySelector('.modal-title').textContent = `Finding: ${finding.title}`;
        
        // Update severity badge in modal
        const severityBadge = modal.querySelector('.finding-severity-badge');
        if (severityBadge) {
            severityBadge.className = `badge severity-${finding.severity} finding-severity-badge`;
            severityBadge.textContent = finding.severity.charAt(0).toUpperCase() + finding.severity.slice(1);
        }
    }

    createFinding() {
        const form = document.getElementById('createFindingForm');
        const formData = new FormData(form);
        
        // Add rich text content
        if (window.createDescriptionEditor) {
            formData.set('description', window.createDescriptionEditor.getContent());
        }
        if (window.createRemediationEditor) {
            formData.set('remediation', window.createRemediationEditor.getContent());
        }
        
        const submitButton = form.querySelector('button[type="submit"]');
        NexusApp.showLoading(submitButton);

        fetch('/secure/finding/create', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (response.ok) {
                NexusApp.showToast('Finding created successfully', 'success');
                bootstrap.Modal.getInstance(document.getElementById('createFindingModal')).hide();
                window.location.reload();
            } else {
                NexusApp.showToast('Failed to create finding', 'danger');
            }
        })
        .catch(error => {
            console.error('Error creating finding:', error);
            NexusApp.showToast('Error creating finding', 'danger');
        })
        .finally(() => {
            NexusApp.hideLoading(submitButton);
        });
    }

    saveFindingDetails() {
        const form = document.getElementById('editFindingForm');
        const formData = new FormData(form);
        const findingId = formData.get('finding_id');
        
        // Add rich text content
        if (window.findingDescriptionEditor) {
            formData.set('description', window.findingDescriptionEditor.getContent());
        }
        if (window.findingRemediationEditor) {
            formData.set('remediation', window.findingRemediationEditor.getContent());
        }
        
        const submitButton = form.querySelector('button[type="submit"]');
        NexusApp.showLoading(submitButton);

        fetch(`/secure/finding/${findingId}/edit`, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                NexusApp.showToast('Finding updated successfully', 'success');
                bootstrap.Modal.getInstance(document.getElementById('findingDetailModal')).hide();
                window.location.reload();
            } else {
                NexusApp.showToast('Failed to update finding', 'danger');
            }
        })
        .catch(error => {
            console.error('Error updating finding:', error);
            NexusApp.showToast('Error updating finding', 'danger');
        })
        .finally(() => {
            NexusApp.hideLoading(submitButton);
        });
    }

    deleteFinding(findingId) {
        if (!confirm('Are you sure you want to delete this finding? This action cannot be undone.')) {
            return;
        }

        fetch(`/secure/finding/${findingId}/delete`, {
            method: 'POST'
        })
        .then(response => {
            if (response.ok) {
                NexusApp.showToast('Finding deleted successfully', 'success');
                window.location.reload();
            } else {
                NexusApp.showToast('Failed to delete finding', 'danger');
            }
        })
        .catch(error => {
            console.error('Error deleting finding:', error);
            NexusApp.showToast('Error deleting finding', 'danger');
        });
    }

    setupSearch() {
        const searchInput = document.getElementById('findingSearch');
        if (!searchInput) return;

        const debouncedSearch = NexusApp.debounce((query) => {
            this.searchFindings(query);
        }, 300);

        searchInput.addEventListener('input', (e) => {
            debouncedSearch(e.target.value);
        });
    }

    searchFindings(query) {
        const findings = document.querySelectorAll('.finding-item');
        const searchTerm = query.toLowerCase().trim();

        findings.forEach(finding => {
            const title = finding.querySelector('.finding-title').textContent.toLowerCase();
            const description = finding.querySelector('.finding-description')?.textContent.toLowerCase() || '';
            
            const matches = title.includes(searchTerm) || description.includes(searchTerm);
            
            // Only show if it matches search AND current filters
            const currentlyVisible = finding.style.display !== 'none';
            finding.style.display = matches && (searchTerm === '' || currentlyVisible) ? '' : 'none';
        });

        // Update results count
        const visibleCount = document.querySelectorAll('.finding-item[style=""], .finding-item:not([style])').length;
        const resultsCount = document.getElementById('resultsCount');
        if (resultsCount) {
            resultsCount.textContent = `${visibleCount} finding${visibleCount !== 1 ? 's' : ''}`;
        }
    }

    setupPagination() {
        // Handle pagination if implemented
        const paginationLinks = document.querySelectorAll('.pagination .page-link');
        paginationLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                // Preserve current filters in pagination
                const url = new URL(link.href);
                Object.keys(this.currentFilters).forEach(key => {
                    if (this.currentFilters[key]) {
                        url.searchParams.set(key, this.currentFilters[key]);
                    }
                });
                link.href = url.toString();
            });
        });
    }

    initializeRichTextEditor() {
        // Initialize TinyMCE for rich text editing
        if (typeof tinymce !== 'undefined') {
            const editorConfig = {
                selector: '.rich-text-editor',
                height: 300,
                menubar: false,
                plugins: 'advlist autolink lists link charmap preview anchor searchreplace visualblocks code fullscreen table wordcount',
                toolbar: 'undo redo | formatselect | bold italic backcolor | alignleft aligncenter alignright alignjustify | bullist numlist outdent indent | removeformat | code',
                content_style: 'body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-size: 14px; }',
                branding: false,
                setup: function(editor) {
                    editor.on('init', function() {
                        // Store editor references globally for access
                        if (editor.targetElm.id === 'createFindingDescription') {
                            window.createDescriptionEditor = editor;
                        } else if (editor.targetElm.id === 'createFindingRemediation') {
                            window.createRemediationEditor = editor;
                        } else if (editor.targetElm.id === 'findingDetailDescription') {
                            window.findingDescriptionEditor = editor;
                        } else if (editor.targetElm.id === 'findingDetailRemediation') {
                            window.findingRemediationEditor = editor;
                        }
                    });
                }
            };

            tinymce.init(editorConfig);
        }
    }

    generateReport() {
        const generateBtn = document.getElementById('generateReportBtn');
        if (generateBtn) {
            NexusApp.showLoading(generateBtn);
            
            // Open report in new window
            window.open(`/reports/pentest/${this.projectId}/pdf`, '_blank');
            
            setTimeout(() => {
                NexusApp.hideLoading(generateBtn);
                NexusApp.showToast('Report generation started', 'info');
            }, 1000);
        }
    }

    previewReport() {
        window.open(`/reports/preview/pentest/${this.projectId}`, '_blank');
    }
}

// Initialize findings manager when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    const findingsContainer = document.querySelector('.findings-container');
    if (findingsContainer) {
        const projectId = findingsContainer.getAttribute('data-project-id');
        window.findingsManager = new FindingsManager(projectId);
    }

    // Setup global delete handlers
    document.addEventListener('click', function(e) {
        if (e.target.matches('.delete-finding-btn')) {
            const findingId = e.target.getAttribute('data-finding-id');
            if (window.findingsManager) {
                window.findingsManager.deleteFinding(findingId);
            }
        }

        if (e.target.matches('#generateReportBtn')) {
            if (window.findingsManager) {
                window.findingsManager.generateReport();
            }
        }

        if (e.target.matches('#previewReportBtn')) {
            if (window.findingsManager) {
                window.findingsManager.previewReport();
            }
        }
    });
});
