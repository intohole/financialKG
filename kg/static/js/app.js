// DOMContentLoaded event listener to initialize the app
document.addEventListener('DOMContentLoaded', () => {
    // Initialize navigation
    initializeNavigation();
    
    // Load the default page (home)
    loadPage('home');
});

// Initialize navigation click handlers
function initializeNavigation() {
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link, .dropdown-item');
    
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            
            // Get the target page from data attribute
            const pageId = link.getAttribute('data-page');
            if (!pageId) {
                return;
            }
            
            // Close dropdown if it's open (for mobile)
            const dropdown = link.closest('.dropdown');
            const dropdownToggle = dropdown ? dropdown.querySelector('.dropdown-toggle') : null;
            
            if (dropdownToggle) {
                const bsDropdown = new bootstrap.Dropdown(dropdownToggle);
                bsDropdown.hide();
            }
            
            // Load the requested page
            loadPage(pageId);
        });
    });
}

// Load a specific page
function loadPage(pageId) {
    // Hide all page content sections
    const allPages = document.querySelectorAll('.page-content');
    allPages.forEach(page => {
        page.classList.remove('active');
    });
    
    // Remove active class from all navigation links
    const allLinks = document.querySelectorAll('.navbar-nav .nav-link, .dropdown-item');
    allLinks.forEach(link => {
        link.classList.remove('active');
    });
    
    // Show the requested page
    const targetPage = document.getElementById(pageId);
    if (targetPage) {
        targetPage.classList.add('active');
    }
    
    // Add active class to the corresponding navigation link
    const targetLink = document.querySelector(`[data-page="${pageId}"]`);
    if (targetLink) {
        targetLink.classList.add('active');
    }
    
    // Call page-specific initialization if available
    if (!pageId) {
        return;
    }
    const pageName = pageId.replace('page-', '');
    const initFunction = window[`init${capitalizeFirstLetter(pageName)}Page`];
    if (initFunction && typeof initFunction === 'function') {
        initFunction();
    }
}

// Capitalize first letter of a string
function capitalizeFirstLetter(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
}

// Utility function for making API requests
async function apiRequest(url, method = 'GET', data = null) {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json'
        }
    };
    
    if (data !== null) {
        options.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(url, options);
        
        if (!response.ok) {
            // Try to get error message from response
            let errorMessage = `HTTP error! status: ${response.status}`;
            try {
                const errorData = await response.json();
                errorMessage = errorData.detail || errorMessage;
            } catch (err) {
                // If response is not JSON, use status text
                errorMessage = response.statusText || errorMessage;
            }
            throw new Error(errorMessage);
        }
        
        // Check if response has content
        if (response.status === 204) {
            return null; // No content
        }
        
        return await response.json();
    } catch (error) {
        console.error('API Request Error:', error);
        showAlert('danger', `API Error: ${error.message}`);
        throw error;
    }
}

// Show an alert message
function showAlert(type, message) {
    // Create alert element
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
    
    // Insert alert at the top of main content
    const mainContent = document.querySelector('main .container');
    mainContent.insertAdjacentHTML('afterbegin', alertHtml);
    
    // Automatically close the alert after 5 seconds
    setTimeout(() => {
        const alert = document.querySelector('.alert');
        if (alert) {
            const bsAlert = bootstrap.Alert.getInstance(alert);
            bsAlert.close();
        }
    }, 5000);
}

// Show loading state for a button
function showButtonLoading(button, text = 'Loading...') {
    button.disabled = true;
    button.innerHTML = `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> ${text}`;
    return button;
}

// Hide loading state for a button
function hideButtonLoading(button, originalText) {
    button.disabled = false;
    button.innerHTML = originalText;
    return button;
}

// Show loading overlay for a section
function showLoadingOverlay(containerId) {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `
            <div class="d-flex justify-content-center align-items-center" style="min-height: 200px;">
                <div class="spinner-border" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
            </div>
        `;
    }
}

// Format JSON data for display
function formatJson(data) {
    try {
        return JSON.stringify(data, null, 2);
    } catch (error) {
        return String(data);
    }
}

// Add click event listener to all delete buttons
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('btn-delete')) {
        e.preventDefault();
        
        const url = e.target.getAttribute('data-url');
        const itemName = e.target.getAttribute('data-name') || 'this item';
        const successCallback = e.target.getAttribute('data-success-callback');
        
        if (confirm(`Are you sure you want to delete ${itemName}?`)) {
            apiRequest(url, 'DELETE')
                .then(() => {
                    showAlert('success', `${itemName} deleted successfully`);
                    
                    // Call success callback if provided
                    if (successCallback && window[successCallback]) {
                        window[successCallback]();
                    } else {
                        // Reload the current page by default
                        const activePage = document.querySelector('.page-content.active');
                        if (activePage) {
                            loadPage(activePage.id);
                        }
                    }
                })
                .catch(error => {
                    // Error already handled by apiRequest
                });
        }
    }
});

// Function to format date
function formatDate(dateString) {
    if (!dateString) return '';
    
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

// Function to copy text to clipboard
function copyToClipboard(text) {
    navigator.clipboard.writeText(text)
        .then(() => {
            showAlert('success', 'Copied to clipboard!');
        })
        .catch(err => {
            console.error('Could not copy text: ', err);
            showAlert('danger', 'Failed to copy to clipboard');
        });
}

// 暴露全局函数
window.formatDate = formatDate;
window.copyToClipboard = copyToClipboard;

// Initialize all page scripts
// These will be called when their respective pages are loaded

// Example page initialization function (to be implemented in individual files)
function initHomePage() {
    // Home page specific initialization
    console.log('Home page initialized');
}

// Entity page initialization will be in entity.js
// Relation page initialization will be in relation.js
// AutoKG page initialization will be in autokg.js
// Deduplication page initialization will be in deduplication.js
// Visualization page initialization will be in visualization.js
// News page initialization will be in news.js