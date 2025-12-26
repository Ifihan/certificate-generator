// State management
let uploadedFile = false;
let hasProgress = false;
let isComplete = false;

// Check for existing progress on page load
async function checkExistingProgress() {
    try {
        const response = await fetch('/check-progress');
        const { has_progress, processed_count, results, has_csv, csv_matches, is_complete } = await response.json();

        if (has_progress) {
            hasProgress = true;
            document.getElementById('progressInfo').classList.remove('hidden');
            document.getElementById('progressCount').textContent = processed_count;

            if (results?.length) {
                displayResults(results, false);
                isComplete = is_complete;
            }

            // Show and configure generate/continue buttons
            document.getElementById('btnGroup').classList.remove('hidden');
            const generateBtn = document.getElementById('generateBtn');
            const continueBtn = document.getElementById('continueBtn');

            if (isComplete) {
                generateBtn.classList.remove('hidden');
                continueBtn.classList.add('hidden');
                generateBtn.disabled = false;
                document.getElementById('resetBtn').classList.remove('hidden');
            } else if (has_csv && csv_matches) {
                // Show Continue button when there's progress and CSV matches
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
                // No CSV available - show Continue button but disabled
                generateBtn.classList.add('hidden');
                continueBtn.classList.remove('hidden');
                continueBtn.disabled = true;
                document.getElementById('resetBtn').classList.remove('hidden');
            }
        } else {
            // NO PROGRESS - Clear any stale data from DOM
            hasProgress = false;
            isComplete = false;
            displayedNames.clear();
            document.getElementById('progressInfo').classList.add('hidden');
            document.getElementById('results').innerHTML = '';
            document.getElementById('btnGroup').classList.add('hidden');
            document.getElementById('resetBtn').classList.add('hidden');

            // Clear any status messages
            const status = document.getElementById('status');
            status.className = 'status';
            status.innerHTML = '';
        }
    } catch (e) {
        console.error('Progress check failed:', e);
    }
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
    const status = document.getElementById('status');

    // Disable both buttons during generation
    generateBtn.disabled = true;
    continueBtn.disabled = true;

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
                document.getElementById('progressInfo').classList.add('hidden');
                addDownloadButton();
            } else {
                hasProgress = true;
                generateBtn.classList.add('hidden');
                continueBtn.classList.remove('hidden');
                continueBtn.disabled = false;
            }
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
            document.getElementById('progressInfo').classList.add('hidden');
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

// Initialize on page load
window.addEventListener('DOMContentLoaded', () => {
    checkExistingProgress();
});

// Abort active generation on page unload
window.addEventListener('beforeunload', () => {
    if (activeGenerationController) {
        activeGenerationController.abort();
    }
});
