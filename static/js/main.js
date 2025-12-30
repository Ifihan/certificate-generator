// State management
let uploadedFile = false;
let hasProgress = false;
let isComplete = false;

// Settings state
let currentSettings = {};
let settingsExpanded = true; // Start expanded by default
let previewDebounceTimer = null;

// Check for existing progress on page load
async function checkExistingProgress() {
    try {
        const response = await fetch('/check-progress');
        const { has_progress, processed_count, results, has_csv, csv_matches, is_complete, is_generating } = await response.json();

        if (has_progress) {
            hasProgress = true;

            if (results?.length) {
                displayResults(results, false);
                isComplete = is_complete;
            }

            document.getElementById('btnGroup').classList.remove('hidden');
            const generateBtn = document.getElementById('generateBtn');
            const continueBtn = document.getElementById('continueBtn');
            const status = document.getElementById('status');

            if (is_generating) {
                generateBtn.classList.add('hidden');
                continueBtn.classList.remove('hidden');
                continueBtn.disabled = true;
                status.className = 'status show loading';
                status.innerHTML = `<div class="spinner"></div>Generation in progress... ${processed_count} certificate(s) generated so far.`;
                document.getElementById('cancelBtn').classList.remove('hidden');
                document.getElementById('resetBtn').classList.add('hidden');

                startPollingForProgress(processed_count);
            } else if (isComplete) {
                generateBtn.classList.remove('hidden');
                continueBtn.classList.add('hidden');
                generateBtn.disabled = false;
                document.getElementById('resetBtn').classList.remove('hidden');
            } else if (has_csv && csv_matches) {
                generateBtn.classList.add('hidden');
                continueBtn.classList.remove('hidden');
                continueBtn.disabled = false;
                uploadedFile = true;
                document.getElementById('resetBtn').classList.remove('hidden');
            } else if (has_csv && !csv_matches) {
                generateBtn.classList.remove('hidden');
                continueBtn.classList.add('hidden');
                generateBtn.textContent = 'Generate with Current CSV';
                generateBtn.disabled = false;
                document.getElementById('resetBtn').classList.remove('hidden');
            } else {
                generateBtn.classList.add('hidden');
                continueBtn.classList.remove('hidden');
                continueBtn.disabled = true;
                document.getElementById('resetBtn').classList.remove('hidden');
            }
        } else {
            hasProgress = false;
            isComplete = false;
            displayedNames.clear();
            document.getElementById('results').innerHTML = '';
            document.getElementById('btnGroup').classList.add('hidden');
            document.getElementById('resetBtn').classList.add('hidden');

            const status = document.getElementById('status');
            status.className = 'status';
            status.innerHTML = '';
        }
    } catch (e) {
        console.error('Progress check failed:', e);
    }
}

function startPollingForProgress(initialCount = 0) {
    let currentCount = initialCount;
    const status = document.getElementById('status');

    const pollInterval = setInterval(async () => {
        try {
            const response = await fetch('/check-progress');
            const data = await response.json();

            if (!data.is_generating) {
                clearInterval(pollInterval);
                location.reload();
            }

            if (data.results && data.results.length > 0) {
                currentCount = data.processed_count;
                status.innerHTML = `<div class="spinner"></div>Generation in progress... ${currentCount} certificate(s) generated so far.`;

                for (const result of data.results) {
                    if (!displayedNames.has(result.name)) {
                        appendResultWithAnimation(result);
                        displayedNames.add(result.name);
                    }
                }
            }
        } catch (e) {
            console.error('Progress poll error:', e);
        }
    }, 500);
}

// Handle file upload
async function handleFileSelect(event) {
    const file = event.target.files[0];
    if (!file) return;

    const status = document.getElementById('status');
    const generateBtn = document.getElementById('generateBtn');
    const continueBtn = document.getElementById('continueBtn');
    const resetBtn = document.getElementById('resetBtn');

    document.getElementById('fileInfo').textContent = `Selected: ${file.name}`;
    status.className = 'status show loading';
    status.innerHTML = '<div class="spinner"></div>Uploading and validating...';

    try {
        const formData = new FormData();
        formData.append('file', file);
        const response = await fetch('/upload-csv', { method: 'POST', body: formData });
        const data = await response.json();

        if (data.success) {
            uploadedFile = true;
            document.getElementById('btnGroup').classList.remove('hidden');

            if (data.is_new_csv) {
                status.className = 'status show warning';
                status.innerHTML = `<strong>New CSV uploaded</strong><br>
                    You have ${data.previous_progress} certificates from a previous CSV.<br>
                    Click "Start Fresh" to clear old progress and use this new CSV.`;
                generateBtn.classList.remove('hidden');
                continueBtn.classList.add('hidden');
                generateBtn.disabled = true;
                resetBtn.classList.remove('hidden');
            } else {
                status.className = 'status show success';
                status.innerHTML = `✓ ${data.message}`;

                if (hasProgress && !isComplete) {
                    // Show Continue button for resuming
                    generateBtn.classList.add('hidden');
                    continueBtn.classList.remove('hidden');
                    continueBtn.disabled = false;
                    resetBtn.classList.remove('hidden');
                } else {
                    // Show Generate button for fresh start
                    generateBtn.classList.remove('hidden');
                    continueBtn.classList.add('hidden');
                    generateBtn.disabled = false;
                }
            }
        } else {
            status.className = 'status show error';
            status.innerHTML = `<strong>Error:</strong> ${data.error}`;
        }
    } catch (e) {
        status.className = 'status show error';
        status.innerHTML = `<strong>Error:</strong> ${e.message}`;
    }
}

// Track which names we've already shown
let displayedNames = new Set();

// Track active generation controller
let activeGenerationController = null;

// Generate certificates with real-time progress polling
async function generateCertificates() {
    if (!uploadedFile && !hasProgress) {
        alert('Please upload a CSV file first');
        return;
    }

    const generateBtn = document.getElementById('generateBtn');
    const continueBtn = document.getElementById('continueBtn');
    const cancelBtn = document.getElementById('cancelBtn');
    const resetBtn = document.getElementById('resetBtn');
    const status = document.getElementById('status');

    // Disable both buttons during generation
    generateBtn.disabled = true;
    continueBtn.disabled = true;

    // Show Cancel button, hide Reset button
    cancelBtn.classList.remove('hidden');
    cancelBtn.disabled = false;
    resetBtn.classList.add('hidden');

    status.className = 'status show loading';
    status.innerHTML = '<div class="spinner"></div>Generating certificates...';

    // Get current progress to avoid showing old certificates
    const initialProgress = await fetch('/check-progress').then(r => r.json());

    // Mark existing certificates as already displayed
    if (initialProgress.results) {
        initialProgress.results.forEach(r => displayedNames.add(r.name));
    }

    // Track new certificates in this session
    let newInThisSession = 0;

    // Create abort controller to cancel requests on page unload
    activeGenerationController = new AbortController();

    // Start generation in background (don't wait for response)
    const generatePromise = fetch('/generate', {
        method: 'POST',
        signal: activeGenerationController.signal
    });

    // Poll for progress while generation is happening
    const pollInterval = setInterval(async () => {
        try {
            const response = await fetch('/check-progress', {
                signal: activeGenerationController.signal
            });
            const data = await response.json();

            if (data.results && data.results.length > 0) {
                // Show only new results we haven't displayed yet
                for (const result of data.results) {
                    if (!displayedNames.has(result.name)) {
                        appendResultWithAnimation(result);
                        displayedNames.add(result.name);
                        newInThisSession++;

                        // Update status with count of new certificates
                        status.innerHTML = `<div class="spinner"></div>Generated ${newInThisSession} new certificate(s)...`;
                    }
                }
            }
        } catch (e) {
            if (e.name === 'AbortError') {
                console.log('Generation aborted');
            } else {
                console.error('Progress poll error:', e);
            }
        }
    }, 500); // Poll every 500ms

    try {
        // Wait for generation to complete
        const response = await generatePromise;
        const data = await response.json();

        // Stop polling
        clearInterval(pollInterval);

        if (data.success) {
            // Show any final results we might have missed
            if (data.results && data.results.length > 0) {
                for (const result of data.results) {
                    if (!displayedNames.has(result.name)) {
                        appendResultWithAnimation(result);
                        displayedNames.add(result.name);
                    }
                }
            }

            status.className = 'status show success';
            const previousCount = data.results.length - data.new_results.length;
            if (previousCount > 0) {
                status.innerHTML = `<strong>Success!</strong> Generated ${data.new_results.length} new certificate(s). Previously generated: ${previousCount}. Total: ${data.results.length}`;
            } else {
                status.innerHTML = `<strong>Success!</strong> Generated ${data.new_results.length} certificate(s).`;
            }

            // Show download button if completed
            if (data.completed) {
                isComplete = true;
                generateBtn.classList.remove('hidden');
                continueBtn.classList.add('hidden');
                generateBtn.disabled = false;
                addDownloadButton();
            } else {
                hasProgress = true;
                generateBtn.classList.add('hidden');
                continueBtn.classList.remove('hidden');
                continueBtn.disabled = false;
            }

            // Hide Cancel button, show Reset button
            cancelBtn.classList.add('hidden');
            resetBtn.classList.remove('hidden');
        } else {
            throw new Error(data.error);
        }
    } catch (e) {
        clearInterval(pollInterval);
        status.className = 'status show error';
        status.innerHTML = `<strong>Error:</strong> ${e.message}`;

        // Re-enable whichever button was visible
        if (!generateBtn.classList.contains('hidden')) {
            generateBtn.disabled = false;
        }
        if (!continueBtn.classList.contains('hidden')) {
            continueBtn.disabled = false;
        }

        // Hide Cancel button, show Reset button
        cancelBtn.classList.add('hidden');
        resetBtn.classList.remove('hidden');
    } finally {
        activeGenerationController = null;
    }
}

// Helper function to add a small delay
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Append a single result with animation
function appendResultWithAnimation(result) {
    const resultsContainer = document.getElementById('results');

    const resultDiv = document.createElement('div');
    resultDiv.className = `result-item ${result.status === 'error' ? 'error' : ''}`;
    resultDiv.style.opacity = '0';
    resultDiv.style.transform = 'translateY(-10px)';
    resultDiv.style.transition = 'all 0.3s ease';

    resultDiv.innerHTML = `
        <div class="result-name">✓ Generated for ${result.name}</div>
        <div class="result-url">
            ${result.status === 'error'
                ? `<span style="color:#dc2626">Error: ${result.error || 'Unknown'}</span>`
                : `<a href="${result.url}" target="_blank">${result.url}</a>`
            }
        </div>
    `;

    resultsContainer.appendChild(resultDiv);

    // Trigger animation
    setTimeout(() => {
        resultDiv.style.opacity = '1';
        resultDiv.style.transform = 'translateY(0)';
    }, 10);

    // Auto-scroll to show the new result
    resultsContainer.scrollTop = resultsContainer.scrollHeight;
}

// Add download button
function addDownloadButton() {
    const resultsContainer = document.getElementById('results');
    if (!document.getElementById('downloadBtn')) {
        const downloadBtn = document.createElement('button');
        downloadBtn.id = 'downloadBtn';
        downloadBtn.className = 'btn btn-secondary';
        downloadBtn.style.marginTop = '16px';
        downloadBtn.textContent = 'Download CSV';
        downloadBtn.onclick = downloadCSV;
        resultsContainer.appendChild(downloadBtn);
    }
}

// Display results
function displayResults(results, showDownload) {
    const resultsContainer = document.getElementById('results');
    const resultItems = results.map(r => {
        // Track displayed names
        displayedNames.add(r.name);

        return `
            <div class="result-item ${r.status === 'error' ? 'error' : ''}">
                <div class="result-name">${r.name}</div>
                <div class="result-url">
                    ${r.status === 'error'
                        ? `<span style="color:#dc2626">Error: ${r.error || 'Unknown'}</span>`
                        : `<a href="${r.url}" target="_blank">${r.url}</a>`
                    }
                </div>
            </div>
        `;
    }).join('');

    const downloadButton = showDownload
        ? '<button class="btn btn-secondary" onclick="downloadCSV()" style="margin-top:16px">Download CSV</button>'
        : '';

    resultsContainer.innerHTML = resultItems + downloadButton;

    // Scroll to bottom when loading existing results
    resultsContainer.scrollTop = resultsContainer.scrollHeight;
}

// Cancel generation
async function cancelGeneration() {
    const status = document.getElementById('status');
    const cancelBtn = document.getElementById('cancelBtn');

    cancelBtn.disabled = true;
    status.className = 'status show warning';
    status.innerHTML = 'Cancelling generation...';

    try {
        const response = await fetch('/cancel-generation', { method: 'POST' });
        const data = await response.json();

        if (data.success) {
            status.className = 'status show warning';
            status.innerHTML = 'Generation cancelled. Progress has been saved.';
        } else {
            throw new Error(data.error);
        }
    } catch (e) {
        status.className = 'status show error';
        status.innerHTML = `<strong>Error:</strong> ${e.message}`;
        cancelBtn.disabled = false;
    }
}

// Reset progress
async function resetProgress() {
    if (!confirm('This will clear all generated certificates. Are you sure?')) return;

    const status = document.getElementById('status');

    status.className = 'status show loading';
    status.innerHTML = '<div class="spinner"></div>Clearing progress...';

    try {
        const response = await fetch('/reset-progress', { method: 'POST' });
        const data = await response.json();

        if (data.success) {
            // COMPLETELY reset ALL state
            hasProgress = false;
            isComplete = false;
            uploadedFile = false;
            displayedNames.clear();

            // Clear UI
            status.className = 'status show success';
            status.innerHTML = '✓ Progress cleared. Upload a CSV to start fresh.';
            document.getElementById('results').innerHTML = '';
            document.getElementById('btnGroup').classList.add('hidden');
            document.getElementById('resetBtn').classList.add('hidden');
            document.getElementById('fileInfo').textContent = 'No file selected';
        } else {
            throw new Error(data.error);
        }
    } catch (e) {
        status.className = 'status show error';
        status.innerHTML = `<strong>Error:</strong> ${e.message}`;
    }
}

// Download CSV
function downloadCSV() {
    window.location.href = '/download-csv';
}

// Setup drag and drop
function setupDragAndDrop() {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('csvFile');

    // Prevent default drag behaviors on the whole document
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        document.body.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
        });
    });

    // Highlight drop zone when dragging over it
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => {
            dropZone.classList.add('drag-over');
        });
    });

    // Remove highlight when leaving or dropping
    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => {
            dropZone.classList.remove('drag-over');
        });
    });

    // Handle dropped files
    dropZone.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            const file = files[0];
            if (file.name.endsWith('.csv')) {
                // Create a new FileList-like object and trigger handleFileSelect
                const dataTransfer = new DataTransfer();
                dataTransfer.items.add(file);
                fileInput.files = dataTransfer.files;
                handleFileSelect({ target: fileInput });
            } else {
                const status = document.getElementById('status');
                status.className = 'status show error';
                status.innerHTML = '<strong>Error:</strong> Please upload a CSV file';
            }
        }
    });

    // Make the whole drop zone clickable
    dropZone.addEventListener('click', (e) => {
        // Don't trigger if clicking on the label or button inside
        if (e.target.closest('.upload-label')) return;
        fileInput.click();
    });
}

// Initialize on page load
window.addEventListener('DOMContentLoaded', () => {
    checkExistingProgress();
    setupDragAndDrop();
    loadSettings();
    setupMarkerDrag();
});

// Abort active generation on page unload
window.addEventListener('beforeunload', () => {
    if (activeGenerationController) {
        activeGenerationController.abort();
    }
});

// ============ Settings Functions ============

// Toggle settings panel
function toggleSettings() {
    settingsExpanded = !settingsExpanded;
    const content = document.getElementById('settingsContent');
    const chevron = document.getElementById('settingsChevron');

    if (settingsExpanded) {
        content.classList.add('expanded');
        chevron.style.transform = 'rotate(180deg)';
        updatePreview();
    } else {
        content.classList.remove('expanded');
        chevron.style.transform = 'rotate(0deg)';
    }
}

// Load settings from server
async function loadSettings() {
    try {
        const [settingsRes, templatesRes, fontsRes] = await Promise.all([
            fetch('/api/settings'),
            fetch('/api/templates'),
            fetch('/api/fonts')
        ]);

        currentSettings = await settingsRes.json();
        const { templates } = await templatesRes.json();
        const { fonts } = await fontsRes.json();

        // Populate template dropdown
        const templateSelect = document.getElementById('templateSelect');
        if (templates && templates.length > 0) {
            templateSelect.innerHTML = templates.map(t =>
                `<option value="${t.filename}" ${t.filename === currentSettings.template ? 'selected' : ''}>${t.name}</option>`
            ).join('');

            // Ensure the saved template is selected, or fall back to first available
            if (!templateSelect.value || !templates.find(t => t.filename === templateSelect.value)) {
                templateSelect.value = templates[0].filename;
            }
        } else {
            templateSelect.innerHTML = '<option value="">No templates available - upload one</option>';
        }

        // Populate font dropdown
        const fontSelect = document.getElementById('fontSelect');
        if (fonts && fonts.length > 0) {
            fontSelect.innerHTML = fonts.map(f =>
                `<option value="${f.path}" ${f.path === currentSettings.font_path ? 'selected' : ''}>${f.name}</option>`
            ).join('');

            // Ensure the saved font is selected, or fall back to first available
            if (!fontSelect.value || !fonts.find(f => f.path === fontSelect.value)) {
                fontSelect.value = fonts[0].path;
            }
        } else {
            fontSelect.innerHTML = '<option value="">No fonts available - upload one</option>';
        }

        // Set other values
        document.getElementById('fontSizeSlider').value = currentSettings.font_size;
        document.getElementById('fontSizeValue').textContent = currentSettings.font_size;

        document.getElementById('strokeWidthSlider').value = currentSettings.stroke_width;
        document.getElementById('strokeWidthValue').textContent = currentSettings.stroke_width;

        // Convert RGB to hex for color picker
        const color = currentSettings.text_color;
        const hexColor = rgbToHex(color[0], color[1], color[2]);
        document.getElementById('textColor').value = hexColor;
        document.getElementById('textColorHex').textContent = hexColor.toUpperCase();

        // Set position values
        document.getElementById('posXValue').textContent = Math.round(currentSettings.text_x_position * 100);
        document.getElementById('posYValue').textContent = Math.round(currentSettings.text_y_position * 100);

        // Expand settings panel by default and load preview
        const content = document.getElementById('settingsContent');
        const chevron = document.getElementById('settingsChevron');
        content.classList.add('expanded');
        chevron.style.transform = 'rotate(180deg)';
        settingsExpanded = true;

        // Load preview only if we have a template
        if (templates && templates.length > 0) {
            updatePreview();
        }

    } catch (e) {
        console.error('Failed to load settings:', e);
    }
}

// Save settings to server
async function saveSettings() {
    const saveBtn = document.getElementById('saveSettingsBtn');
    saveBtn.disabled = true;
    saveBtn.textContent = 'Saving...';

    try {
        const settings = getCurrentFormSettings();

        const response = await fetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(settings)
        });

        const data = await response.json();

        if (data.success) {
            currentSettings = data.settings;
            saveBtn.textContent = 'Saved!';

            // Collapse settings panel after a short delay
            setTimeout(() => {
                saveBtn.textContent = 'Save Settings';
                saveBtn.disabled = false;

                // Collapse the settings panel
                settingsExpanded = false;
                const content = document.getElementById('settingsContent');
                const chevron = document.getElementById('settingsChevron');
                content.classList.remove('expanded');
                chevron.style.transform = 'rotate(0deg)';

                // Scroll to CSV upload section
                const uploadSection = document.querySelector('.upload-section');
                if (uploadSection) {
                    uploadSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }, 800);
        } else {
            throw new Error(data.error);
        }
    } catch (e) {
        console.error('Failed to save settings:', e);
        saveBtn.textContent = 'Error!';
        setTimeout(() => {
            saveBtn.textContent = 'Save Settings';
            saveBtn.disabled = false;
        }, 1500);
    }
}

// Get current settings from form
function getCurrentFormSettings() {
    const hexColor = document.getElementById('textColor').value;
    const rgb = hexToRgb(hexColor);

    return {
        template: document.getElementById('templateSelect').value,
        font_path: document.getElementById('fontSelect').value,
        font_size: parseInt(document.getElementById('fontSizeSlider').value),
        text_color: [rgb.r, rgb.g, rgb.b],
        stroke_width: parseInt(document.getElementById('strokeWidthSlider').value),
        text_x_position: parseFloat(document.getElementById('posXValue').textContent) / 100,
        text_y_position: parseFloat(document.getElementById('posYValue').textContent) / 100,
        image_quality: currentSettings.image_quality || 95
    };
}

// Called when any setting changes
function onSettingChange() {
    // Update color hex display
    const hexColor = document.getElementById('textColor').value;
    document.getElementById('textColorHex').textContent = hexColor.toUpperCase();

    // Debounce preview update
    if (previewDebounceTimer) {
        clearTimeout(previewDebounceTimer);
    }
    previewDebounceTimer = setTimeout(() => {
        updatePreview();
    }, 300);
}

// Update preview image
async function updatePreview() {
    const previewLoading = document.getElementById('previewLoading');
    const previewImage = document.getElementById('previewImage');
    const positionMarker = document.getElementById('positionMarker');

    // Check if we have a valid template selected
    const templateSelect = document.getElementById('templateSelect');
    if (!templateSelect.value) {
        console.warn('No template selected, skipping preview update');
        previewLoading.style.display = 'none';
        return;
    }

    previewLoading.style.display = 'flex';
    previewImage.style.opacity = '0.5';

    try {
        const settings = getCurrentFormSettings();
        console.log('Updating preview with settings:', settings);

        const response = await fetch('/api/preview', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: 'Sample Name', ...settings })
        });

        const data = await response.json();

        if (data.success) {
            // Force image refresh by adding timestamp to prevent caching
            previewImage.src = data.preview;
            previewImage.style.opacity = '1';

            // Update position marker
            updatePositionMarker();
        } else {
            console.error('Preview generation failed:', data.error);
            // Show a placeholder or error state
            previewImage.alt = 'Preview failed: ' + data.error;
        }
    } catch (e) {
        console.error('Failed to update preview:', e);
    } finally {
        previewLoading.style.display = 'none';
    }
}

// Drag state
let isDragging = false;
let dragMarker = null;

// Setup drag functionality for position marker
function setupMarkerDrag() {
    const marker = document.getElementById('positionMarker');
    const container = document.getElementById('previewContainer');

    // Mouse events
    marker.addEventListener('mousedown', startDrag);
    document.addEventListener('mousemove', onDrag);
    document.addEventListener('mouseup', endDrag);

    // Touch events for mobile
    marker.addEventListener('touchstart', startDrag, { passive: false });
    document.addEventListener('touchmove', onDrag, { passive: false });
    document.addEventListener('touchend', endDrag);
}

function startDrag(event) {
    event.preventDefault();
    isDragging = true;
    dragMarker = document.getElementById('positionMarker');
    dragMarker.classList.add('dragging');
}

function onDrag(event) {
    if (!isDragging) return;
    event.preventDefault();

    const container = document.getElementById('previewContainer');
    const rect = container.getBoundingClientRect();

    // Get position from mouse or touch
    const clientX = event.touches ? event.touches[0].clientX : event.clientX;
    const clientY = event.touches ? event.touches[0].clientY : event.clientY;

    // Calculate percentage position
    const x = ((clientX - rect.left) / rect.width) * 100;
    const y = ((clientY - rect.top) / rect.height) * 100;

    // Clamp values
    const clampedX = Math.max(5, Math.min(95, x));
    const clampedY = Math.max(5, Math.min(95, y));

    // Update marker position immediately (no debounce for smooth dragging)
    dragMarker.style.left = `${clampedX}%`;
    dragMarker.style.top = `${clampedY}%`;

    // Update display values
    document.getElementById('posXValue').textContent = Math.round(clampedX);
    document.getElementById('posYValue').textContent = Math.round(clampedY);
}

function endDrag() {
    if (!isDragging) return;
    isDragging = false;

    if (dragMarker) {
        dragMarker.classList.remove('dragging');
        dragMarker = null;
    }

    // Trigger preview update after drag ends
    onSettingChange();
}

// Update position marker on preview
function updatePositionMarker() {
    const marker = document.getElementById('positionMarker');
    const xPos = parseFloat(document.getElementById('posXValue').textContent);
    const yPos = parseFloat(document.getElementById('posYValue').textContent);

    marker.style.left = `${xPos}%`;
    marker.style.top = `${yPos}%`;
    marker.style.display = 'block';
}

// Upload template file
async function uploadTemplate(event) {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    // Show loading state
    const previewLoading = document.getElementById('previewLoading');
    previewLoading.style.display = 'flex';

    try {
        const response = await fetch('/api/upload-template', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            // Refresh templates and select the new one
            const templatesRes = await fetch('/api/templates');
            const { templates } = await templatesRes.json();

            const templateSelect = document.getElementById('templateSelect');
            templateSelect.innerHTML = templates.map(t =>
                `<option value="${t.filename}" ${t.filename === data.filename ? 'selected' : ''}>${t.name}</option>`
            ).join('');

            // Force the value to be set correctly
            templateSelect.value = data.filename;

            // Update preview immediately with the new template
            await updatePreview();
        } else {
            alert('Upload failed: ' + data.error);
        }
    } catch (e) {
        console.error('Upload failed:', e);
        alert('Upload failed: ' + e.message);
    } finally {
        previewLoading.style.display = 'none';
    }

    // Reset input
    event.target.value = '';
}

// Upload font file
async function uploadFont(event) {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/api/upload-font', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            // Refresh fonts and select the new one
            const fontsRes = await fetch('/api/fonts');
            const { fonts } = await fontsRes.json();

            const fontSelect = document.getElementById('fontSelect');
            fontSelect.innerHTML = fonts.map(f =>
                `<option value="${f.path}" ${f.path === data.path ? 'selected' : ''}>${f.name}</option>`
            ).join('');

            onSettingChange();
        } else {
            alert('Upload failed: ' + data.error);
        }
    } catch (e) {
        console.error('Upload failed:', e);
        alert('Upload failed: ' + e.message);
    }

    // Reset input
    event.target.value = '';
}

// Update font size label
function updateFontSizeLabel() {
    document.getElementById('fontSizeValue').textContent = document.getElementById('fontSizeSlider').value;
}

// Update stroke width label
function updateStrokeWidthLabel() {
    document.getElementById('strokeWidthValue').textContent = document.getElementById('strokeWidthSlider').value;
}

// Helper: RGB to Hex
function rgbToHex(r, g, b) {
    return '#' + [r, g, b].map(x => {
        const hex = x.toString(16);
        return hex.length === 1 ? '0' + hex : hex;
    }).join('');
}

// Helper: Hex to RGB
function hexToRgb(hex) {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16)
    } : { r: 0, g: 0, b: 0 };
}
