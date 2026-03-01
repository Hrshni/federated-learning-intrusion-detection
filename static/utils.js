/**
 * Enhanced Utility JavaScript Functions for Federated IDS
 * Includes Dark Mode, Notifications, API Helpers, and more
 */

// ============================================================
// DARK MODE MANAGER
// ============================================================

const DarkMode = {
    storageKey: 'federated-darkmode',

    /**
     * Initialize dark mode
     */
    init: function() {
        const savedMode = this.get();
        if (savedMode !== null) {
            this.set(savedMode);
        } else {
            // Check system preference
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            this.set(prefersDark);
        }
        
        // Watch for system preference changes
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            this.set(e.matches);
        });
    },

    /**
     * Get dark mode state
     */
    get: function() {
        return localStorage.getItem(this.storageKey) === 'true';
    },

    /**
     * Set dark mode state
     */
    set: function(isDark) {
        localStorage.setItem(this.storageKey, isDark);
        if (isDark) {
            document.documentElement.setAttribute('data-theme', 'dark');
            document.body.classList.add('dark-mode');
        } else {
            document.documentElement.removeAttribute('data-theme');
            document.body.classList.remove('dark-mode');
        }
    },

    /**
     * Toggle dark mode
     */
    toggle: function() {
        this.set(!this.get());
    }
};

// ============================================================
// API HELPER FUNCTIONS
// ============================================================

const API = {
    /**
     * Make a GET request
     * @param {string} url - The endpoint URL
     * @returns {Promise} - Response promise
     */
    get: async function(url) {
        try {
            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include'
            });
            return this._handleResponse(response);
        } catch (error) {
            console.error('API GET Error:', error);
            throw error;
        }
    },

    /**
     * Make a POST request
     * @param {string} url - The endpoint URL
     * @param {object} data - Request body data
     * @returns {Promise} - Response promise
     */
    post: async function(url, data = {}) {
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data),
                credentials: 'include'
            });
            return this._handleResponse(response);
        } catch (error) {
            console.error('API POST Error:', error);
            throw error;
        }
    },

    /**
     * Make a PUT request
     * @param {string} url - The endpoint URL
     * @param {object} data - Request body data
     * @returns {Promise} - Response promise
     */
    put: async function(url, data = {}) {
        try {
            const response = await fetch(url, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data),
                credentials: 'include'
            });
            return this._handleResponse(response);
        } catch (error) {
            console.error('API PUT Error:', error);
            throw error;
        }
    },

    /**
     * Make a DELETE request
     * @param {string} url - The endpoint URL
     * @returns {Promise} - Response promise
     */
    delete: async function(url) {
        try {
            const response = await fetch(url, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include'
            });
            return this._handleResponse(response);
        } catch (error) {
            console.error('API DELETE Error:', error);
            throw error;
        }
    },

    /**
     * Handle API response
     */
    _handleResponse: async function(response) {
        const contentType = response.headers.get('content-type');
        let data;
        
        if (contentType && contentType.includes('application/json')) {
            data = await response.json().catch(() => null);
        } else {
            data = null;
        }
        
        if (!response.ok) {
            throw {
                status: response.status,
                message: data?.error || 'API Error',
                data: data
            };
        }
        
        return data;
    }
};

// ============================================================
// NOTIFICATION SYSTEM - TOAST
// ============================================================

const Toast = {
    /**
     * Show success toast
     */
    success: function(message, duration = 5000) {
        this._show(message, 'success', duration);
    },

    /**
     * Show error toast
     */
    error: function(message, duration = 5000) {
        this._show(message, 'danger', duration);
    },

    /**
     * Show warning toast
     */
    warning: function(message, duration = 5000) {
        this._show(message, 'warning', duration);
    },

    /**
     * Show info toast
     */
    info: function(message, duration = 5000) {
        this._show(message, 'info', duration);
    },

    /**
     * Internal method to show toast
     */
    _show: function(message, type, duration) {
        const container = this._getContainer();
        const toastDiv = document.createElement('div');
        toastDiv.className = `toast toast-${type}`;
        
        const icon = this._getIcon(type);
        toastDiv.innerHTML = `
            <div class="toast-content">
                <span class="toast-icon">${icon}</span>
                <span class="toast-message">${this._escapeHtml(message)}</span>
                <button class="toast-close" aria-label="Close">✕</button>
            </div>
        `;

        container.appendChild(toastDiv);

        const closeModal = () => {
            toastDiv.classList.add('fade-out');
            setTimeout(() => toastDiv.remove(), 300);
        };

        // Auto-remove after duration
        const timer = setTimeout(closeModal, duration);

        // Click to remove
        toastDiv.querySelector('.toast-close').addEventListener('click', () => {
            clearTimeout(timer);
            closeModal();
        });
    },

    /**
     * Get or create notification container
     */
    _getContainer: function() {
        let container = document.getElementById('toastContainer');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toastContainer';
            container.className = 'toast-container';
            document.body.appendChild(container);
        }
        return container;
    },

    /**
     * Get icon for notification type
     */
    _getIcon: function(type) {
        const icons = {
            success: '✓',
            danger: '✕',
            warning: '⚠',
            info: 'ℹ'
        };
        return icons[type] || '•';
    },

    /**
     * Escape HTML to prevent XSS
     */
    _escapeHtml: function(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
};

// Legacy alias for backwards compatibility
const Notification = Toast;

// ============================================================
// FORM UTILITIES
// ============================================================

const Form = {
    /**
     * Get form data as object
     */
    getFormData: function(form) {
        const formData = new FormData(form);
        const data = {};
        for (let [key, value] of formData.entries()) {
            data[key] = value;
        }
        return data;
    },

    /**
     * Clear form validation errors
     */
    clearErrors: function(form) {
        form.querySelectorAll('.is-invalid').forEach(el => {
            el.classList.remove('is-invalid');
        });
        form.querySelectorAll('.invalid-feedback').forEach(el => {
            el.remove();
        });
    },

    /**
     * Show form validation errors
     */
    showErrors: function(form, errors) {
        for (let field in errors) {
            const input = form.elements[field];
            if (input) {
                input.classList.add('is-invalid');
                const feedback = document.createElement('div');
                feedback.className = 'invalid-feedback';
                feedback.textContent = errors[field];
                input.parentElement.appendChild(feedback);
            }
        }
    },

    /**
     * Disable form submit button
     */
    setSubmitDisabled: function(form, disabled) {
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = disabled;
            if (disabled) {
                submitBtn.innerHTML = '<span class="spinner"></span> Processing...';
            } else {
                submitBtn.innerHTML = submitBtn.getAttribute('data-original-text') || 'Submit';
            }
        }
    },

    /**
     * Reset form to initial state
     */
    reset: function(form) {
        form.reset();
        this.clearErrors(form);
    }
};

// ============================================================
// LOCAL STORAGE UTILITIES
// ============================================================

const Storage = {
    /**
     * Store data in localStorage
     */
    set: function(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
        } catch (error) {
            console.error('Storage Error:', error);
        }
    },

    /**
     * Get data from localStorage
     */
    get: function(key) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : null;
        } catch (error) {
            console.error('Storage Error:', error);
            return null;
        }
    },

    /**
     * Remove data from localStorage
     */
    remove: function(key) {
        localStorage.removeItem(key);
    },

    /**
     * Clear all localStorage
     */
    clear: function() {
        localStorage.clear();
    }
};

// Date/Time Utilities
const DateTime = {
    /**
     * Format date
     * @param {Date|string} date - Date to format
     * @param {string} format - Format string (default: 'YYYY-MM-DD HH:mm:ss')
     * @returns {string} - Formatted date
     */
    format: function(date, format = 'YYYY-MM-DD HH:mm:ss') {
        const d = new Date(date);
        
        const dateStr = {
            'YYYY': d.getFullYear(),
            'MM': String(d.getMonth() + 1).padStart(2, '0'),
            'DD': String(d.getDate()).padStart(2, '0'),
            'HH': String(d.getHours()).padStart(2, '0'),
            'mm': String(d.getMinutes()).padStart(2, '0'),
            'ss': String(d.getSeconds()).padStart(2, '0')
        };

        let result = format;
        for (let key in dateStr) {
            result = result.replace(key, dateStr[key]);
        }
        return result;
    },

    /**
     * Get relative time (e.g., "2 hours ago")
     * @param {Date|string} date - Date to compare
     * @returns {string} - Relative time string
     */
    relative: function(date) {
        const d = new Date(date);
        const now = new Date();
        const seconds = Math.floor((now - d) / 1000);

        const intervals = {
            year: 31536000,
            month: 2592000,
            week: 604800,
            day: 86400,
            hour: 3600,
            minute: 60
        };

        for (let key in intervals) {
            const interval = Math.floor(seconds / intervals[key]);
            if (interval >= 1) {
                return `${interval} ${key}${interval > 1 ? 's' : ''} ago`;
            }
        }

        return 'Just now';
    }
};

// ============================================================
// DOM UTILITIES
// ============================================================

const DOM = {
    /**
     * Event delegation
     */
    on: function(selector, event, callback) {
        document.addEventListener(event, function(e) {
            if (e.target.matches(selector)) {
                callback.call(e.target, e);
            }
        });
    },

    /**
     * Toggle element visibility
     */
    toggle: function(element) {
        if (element) {
            element.style.display = 
                element.style.display === 'none' ? '' : 'none';
        }
    },

    /**
     * Add class to element
     */
    addClass: function(element, className) {
        if (element) {
            element.classList.add(className);
        }
    },

    /**
     * Remove class from element
     */
    removeClass: function(element, className) {
        if (element) {
            element.classList.remove(className);
        }
    },

    /**
     * Copy text to clipboard
     */
    copyToClipboard: function(text) {
        navigator.clipboard.writeText(text).then(() => {
            Toast.success('Copied to clipboard');
        }).catch(() => {
            Toast.error('Failed to copy');
        });
    }
};

// ============================================================
// EXPORT UTILITIES  
// ============================================================

const Exporter = {
    /**
     * Export data as CSV
     */
    downloadCSV: function(data, filename = 'export.csv') {
        let csv = '';
        
        if (Array.isArray(data) && data.length > 0) {
            // Headers
            csv = Object.keys(data[0]).join(',') + '\n';
            
            // Data rows
            data.forEach(row => {
                csv += Object.values(row).map(val => 
                    `"${String(val).replace(/"/g, '""')}"`
                ).join(',') + '\n';
            });
        }
        
        this._downloadFile(csv, filename, 'text/csv');
    },

    /**
     * Export data as JSON
     */
    downloadJSON: function(data, filename = 'export.json') {
        const json = JSON.stringify(data, null, 2);
        this._downloadFile(json, filename, 'application/json');
    },

    /**
     * Download file helper
     */
    _downloadFile: function(content, filename, type) {
        const blob = new Blob([content], { type });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
    }
};

// ============================================================
// INITIALIZATION
// ============================================================

document.addEventListener('DOMContentLoaded', function() {
    // Initialize dark mode
    DarkMode.init();
    
    // Setup dark mode toggle button
    const darkModeToggle = document.querySelector('[data-toggle="darkmode"]');
    if (darkModeToggle) {
        darkModeToggle.addEventListener('click', () => {
            DarkMode.toggle();
        });
    }
    
    console.log('Federated IDS enhanced utilities loaded');
});
