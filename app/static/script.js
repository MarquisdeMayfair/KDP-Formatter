/**
 * KDP Formatter - Modern Web UI JavaScript
 */

// Global variables
let selectedFile = null;
let isProcessing = false;
let sessions = [];
let isRedirecting = false;

/**
 * Check system dependencies status
 */
async function checkDependencies() {
    try {
        const response = await fetch('/health');
        const data = await response.json();

        const statusDiv = document.getElementById('status-content');

        if (data.status === 'healthy') {
            statusDiv.innerHTML = '<span class="status-ok">✓ All dependencies installed</span>';
            statusDiv.className = 'status-ok';
        } else if (data.status === 'degraded') {
            statusDiv.innerHTML = `
                <span class="status-warning">⚠ Missing dependencies:</span>
                <ul>${data.missing_dependencies.map(dep => `<li>${dep}</li>`).join('')}</ul>
                <p>Run: <code>${data.installation_command}</code></p>
            `;
            statusDiv.className = 'status-warning';
        } else {
            statusDiv.innerHTML = '<span class="status-error">✗ System error</span>';
            statusDiv.className = 'status-error';
        }
    } catch (error) {
        console.error('Failed to check dependencies:', error);
        const statusDiv = document.getElementById('status-content');
        statusDiv.innerHTML = '<span class="status-error">✗ Failed to check dependencies</span>';
        statusDiv.className = 'status-error';
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeFileUpload();
    initializeFormHandlers();
    loadRecentConversions();
    updateGenerateButton();
    checkDependencies();
});

/**
 * Initialize drag-and-drop file upload functionality
 */
function initializeFileUpload() {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');

    // Click to open file dialog
    dropZone.addEventListener('click', () => {
        fileInput.click();
    });

    // Drag and drop events
    dropZone.addEventListener('dragover', function(e) {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', function(e) {
        e.preventDefault();
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', function(e) {
        e.preventDefault();
        dropZone.classList.remove('dragover');

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileSelection(files[0]);
        }
    });

    // File input change event
    fileInput.addEventListener('change', function(e) {
        if (e.target.files.length > 0) {
            handleFileSelection(e.target.files[0]);
        }
    });

    // Clear file button
    document.getElementById('clear-file').addEventListener('click', clearFile);
}

/**
 * Handle file selection and validation
 */
function handleFileSelection(file) {
    const allowedExtensions = ['.txt', '.docx', '.pdf', '.md'];
    const fileExt = '.' + file.name.split('.').pop().toLowerCase();

    if (!allowedExtensions.includes(fileExt)) {
        showAlert('Invalid file type. Please select a .txt, .docx, .pdf, or .md file.', 'error');
        return;
    }

    if (file.size > 50 * 1024 * 1024) { // 50MB limit
        showAlert('File size too large. Please select a file smaller than 50MB.', 'error');
        return;
    }

    selectedFile = file;
    updateFileDisplay();
    updateGenerateButton();
}

/**
 * Update the file display area
 */
function updateFileDisplay() {
    const dropContent = document.getElementById('drop-content');
    const fileInfo = document.getElementById('file-info');
    const fileName = document.getElementById('file-name');
    const fileSize = document.getElementById('file-size');

    if (selectedFile) {
        fileName.textContent = selectedFile.name;
        fileSize.textContent = formatFileSize(selectedFile.size);
        dropContent.style.display = 'none';
        fileInfo.style.display = 'flex';
    } else {
        dropContent.style.display = 'block';
        fileInfo.style.display = 'none';
    }
}

/**
 * Clear the selected file
 */
function clearFile() {
    selectedFile = null;
    document.getElementById('file-input').value = '';
    updateFileDisplay();
    updateGenerateButton();
}

/**
 * Format file size for display
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Initialize form handlers
 */
function initializeFormHandlers() {
    // AI detection radio buttons
    document.querySelectorAll('input[name="use_ai"]').forEach(radio => {
        radio.addEventListener('change', function() {
            const aiCost = document.getElementById('ai-cost-estimate');
            aiCost.style.display = this.value === 'true' ? 'inline' : 'none';
        });
    });

    // Generate button
    document.getElementById('generate-btn').addEventListener('click', generateDocument);

    // Test formatting button
    document.getElementById('test-formatting-btn').addEventListener('click', generateFormattingTest);

    // Update generate button on form changes
    document.getElementById('config-form').addEventListener('change', updateGenerateButton);
}

/**
 * Update generate button state
 */
function updateGenerateButton() {
    const generateBtn = document.getElementById('generate-btn');
    const hasFile = selectedFile !== null;

    generateBtn.disabled = !hasFile || isProcessing;
    generateBtn.textContent = isProcessing ? 'Generating...' : 'Generate & Validate';
}

/**
 * Generate document from uploaded file
 */
async function generateDocument() {
    if (!selectedFile) {
        showAlert('Please select a file first.', 'warning');
        return;
    }

    if (isProcessing) return;

    // Collect form data
    const formData = new FormData();
    formData.append('file', selectedFile);

    // Get form values
    const outputFormat = document.querySelector('input[name="output_format"]:checked').value;
    const useAi = document.querySelector('input[name="use_ai"]:checked').value === 'true';
    const useDropCaps = document.getElementById('use-drop-caps').checked;
    const pageSize = document.getElementById('page-size').value;
    const margins = document.getElementById('margins').value;
    const formattingStyle = document.querySelector('input[name="formatting_style"]:checked').value;

    formData.append('output_format', outputFormat);
    formData.append('use_ai', useAi);
    formData.append('use_drop_caps', useDropCaps);
    formData.append('page_size', pageSize);
    formData.append('margins', margins);

    // Convert formatting style to boolean flags
    formData.append('use_paragraph_spacing', formattingStyle === 'modern' || formattingStyle === 'no_indent');
    formData.append('disable_indentation', formattingStyle === 'no_indent');

    // Show processing state
    setProcessingState(true);
    isRedirecting = false;

    try {
        const response = await fetch('/convert', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }

        const result = await response.json();

        // Store session info
        addToRecentConversions(result);

        // Complete processing and redirect to preview page
        setProcessingState(false);
        isRedirecting = true;
        window.location.href = result.preview_url;

    } catch (error) {
        console.error('Conversion error:', error);
        showAlert('An error occurred while processing your file. Please try again.', 'error');
        setProcessingState(false);
    }
}

/**
 * Generate formatting test PDF
 */
async function generateFormattingTest() {
    if (isProcessing) return;

    // Get current form configuration
    const useDropCaps = document.getElementById('use-drop-caps').checked;
    const pageSize = document.getElementById('page-size').value;
    const margins = document.getElementById('margins').value;

    // Show processing state
    setProcessingState(true);
    isRedirecting = false;

    try {
        // Build query string with current configuration
        const formattingStyle = document.querySelector('input[name="formatting_style"]:checked').value;
        const params = new URLSearchParams({
            use_drop_caps: useDropCaps,
            page_size: pageSize,
            margins: margins,
            use_paragraph_spacing: (formattingStyle === 'modern' || formattingStyle === 'no_indent'),
            disable_indentation: (formattingStyle === 'no_indent')
        });

        const response = await fetch(`/formatting-test?${params}`);

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }

        const result = await response.json();

        // Store session info
        addToRecentConversions(result);

        // Complete processing and redirect to preview page
        setProcessingState(false);
        isRedirecting = true;
        window.location.href = result.redirect;

    } catch (error) {
        console.error('Formatting test error:', error);
        showAlert('An error occurred while generating the test PDF. Please try again.', 'error');
        setProcessingState(false);
    }
}

/**
 * Set processing state for UI
 */
function setProcessingState(processing) {
    isProcessing = processing;

    const generateBtn = document.getElementById('generate-btn');
    const progressSection = document.getElementById('progress-section');
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');

    if (processing) {
        generateBtn.disabled = true;
        generateBtn.textContent = 'Generating...';

        progressSection.style.display = 'block';
        progressFill.style.width = '0%';
        progressText.textContent = 'Uploading...';

        // Animate progress
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += Math.random() * 15;
            if (progress > 90) progress = 90;
            progressFill.style.width = progress + '%';

            if (!isProcessing) {
                clearInterval(progressInterval);
                progressFill.style.width = '100%';
                progressText.textContent = 'Complete!';
            }
        }, 500);

    } else {
        generateBtn.disabled = false;
        generateBtn.textContent = 'Generate & Validate';
        progressSection.style.display = 'none';
    }
}

/**
 * Add conversion to recent list
 */
function addToRecentConversions(result) {
    const conversion = {
        sessionId: result.session_id,
        filename: result.filename || (selectedFile ? selectedFile.name : 'Unknown'),
        timestamp: Date.now(),
        validationStatus: result.validation_summary ? getOverallStatus(result.validation_summary) : 'unknown'
    };

    sessions.unshift(conversion);

    // Keep only last 10
    if (sessions.length > 10) {
        sessions = sessions.slice(0, 10);
    }

    // Save to localStorage
    localStorage.setItem('kdp_sessions', JSON.stringify(sessions));

    updateRecentConversions();
}

/**
 * Get overall validation status
 */
function getOverallStatus(summary) {
    if (summary.error > 0) return 'error';
    if (summary.fail > 0) return 'fail';
    if (summary.warning > 0) return 'warning';
    return 'pass';
}

/**
 * Load recent conversions from localStorage
 */
function loadRecentConversions() {
    try {
        const stored = localStorage.getItem('kdp_sessions');
        if (stored) {
            sessions = JSON.parse(stored);
            updateRecentConversions();
        }
    } catch (error) {
        console.error('Error loading recent conversions:', error);
    }
}

/**
 * Update recent conversions display
 */
function updateRecentConversions() {
    const container = document.getElementById('recent-list');
    const noRecent = document.querySelector('.no-recent');

    if (sessions.length === 0) {
        container.innerHTML = '<p class="no-recent">No recent conversions</p>';
        return;
    }

    container.innerHTML = '';

    sessions.forEach(session => {
        const item = document.createElement('div');
        item.className = 'recent-item fade-in';

        const statusClass = `status-${session.validationStatus}`;

        item.innerHTML = `
            <div class="recent-info">
                <h4>${session.filename}</h4>
                <div class="recent-meta">
                    ${new Date(session.timestamp).toLocaleString()}
                </div>
            </div>
            <div class="recent-status ${statusClass}">
                ${session.validationStatus.toUpperCase()}
            </div>
        `;

        item.addEventListener('click', () => {
            window.open(`/preview/${session.sessionId}`, '_blank');
        });

        container.appendChild(item);
    });
}

/**
 * Show alert message
 */
function showAlert(message, type = 'info') {
    // Remove existing alerts
    const existingAlerts = document.querySelectorAll('.alert');
    existingAlerts.forEach(alert => alert.remove());

    // Create new alert
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.textContent = message;

    // Style based on type
    alert.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 1000;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        max-width: 400px;
    `;

    // Color based on type
    const colors = {
        success: '#10b981',
        warning: '#f59e0b',
        error: '#ef4444',
        info: '#06b6d4'
    };

    alert.style.backgroundColor = colors[type] || colors.info;
    alert.style.color = 'white';

    document.body.appendChild(alert);

    // Auto-hide after 5 seconds
    setTimeout(() => {
        if (alert.parentNode) {
            alert.remove();
        }
    }, 5000);
}

/**
 * Error handling for unhandled promise rejections
 */
window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
    showAlert('An unexpected error occurred. Please refresh the page and try again.', 'error');
    setProcessingState(false);
});

/**
 * Handle page unload
 */
window.addEventListener('beforeunload', function(event) {
    // Only prevent unload if we're actively processing and not intentionally redirecting
    if (isProcessing && !isRedirecting) {
        event.preventDefault();
        event.returnValue = '';
    }
});
