// AutoKG JavaScript

// Initialize the AutoKG page
function initAutoKGPage() {
    console.log('AutoKG page initialized');
    
    // Set up event listeners
    setupAutoKGEvents();
}

// Set up event listeners for AutoKG functions
function setupAutoKGEvents() {
    // Entity and Relation Extraction form
    const extractForm = document.getElementById('extract-form');
    if (extractForm) {
        extractForm.addEventListener('submit', (e) => {
            e.preventDefault();
            extractEntityRelation();
        });
    }
    
    // Text Processing form
    const textForm = document.getElementById('text-form');
    if (textForm) {
        textForm.addEventListener('submit', (e) => {
            e.preventDefault();
            processText();
        });
    }
    
    // URL News Processing form
    const urlForm = document.getElementById('url-form');
    if (urlForm) {
        urlForm.addEventListener('submit', (e) => {
            e.preventDefault();
            processUrlNews();
        });
    }
    
    // File News Processing form
    const fileForm = document.getElementById('file-form');
    if (fileForm) {
        fileForm.addEventListener('submit', (e) => {
            e.preventDefault();
            processFileNews();
        });
    }
}

// Extract entities and relations from text
async function extractEntityRelation() {
    const form = document.getElementById('extract-form');
    const button = form.querySelector('button[type="submit"]');
    const originalButtonText = button.textContent;
    const resultContainer = document.getElementById('extract-result');
    
    try {
        showButtonLoading(button, 'Extracting...');
        resultContainer.innerHTML = '<div class="loading-container"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>';
        
        const formData = new FormData(form);
        const data = {
            text: formData.get('text')
        };
        
        const result = await apiRequest('/api/v1/autokg/extract-entities', 'POST', data);
        
        // Render the extraction result
        renderExtractionResult(result, resultContainer);
        
    } catch (error) {
        console.error('Error extracting entities and relations:', error);
        // Error already handled by apiRequest
    } finally {
        hideButtonLoading(button, originalButtonText);
    }
}

// Process text to extract entities and relations
async function processText() {
    const form = document.getElementById('text-form');
    const button = form.querySelector('button[type="submit"]');
    const originalButtonText = button.textContent;
    const resultContainer = document.getElementById('text-result');
    
    try {
        showButtonLoading(button, 'Processing...');
        resultContainer.innerHTML = '<div class="loading-container"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>';
        
        const formData = new FormData(form);
        const data = {
            text: formData.get('text')
        };
        
        const result = await apiRequest('/api/v1/autokg/process-text', 'POST', data);
        
        // Render the processing result
        renderProcessingResult(result, resultContainer);
        
    } catch (error) {
        console.error('Error processing text:', error);
        // Error already handled by apiRequest
    } finally {
        hideButtonLoading(button, originalButtonText);
    }
}

// Process URL news to extract entities and relations
async function processUrlNews() {
    const form = document.getElementById('url-form');
    const button = form.querySelector('button[type="submit"]');
    const originalButtonText = button.textContent;
    const resultContainer = document.getElementById('url-result');
    
    try {
        showButtonLoading(button, 'Processing...');
        resultContainer.innerHTML = '<div class="loading-container"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>';
        
        const formData = new FormData(form);
        const data = {
            url: formData.get('url')
        };
        
        const result = await apiRequest('/api/v1/autokg/process-news', 'POST', data);
        
        // Render the URL processing result
        renderProcessingResult(result, resultContainer);
        
    } catch (error) {
        console.error('Error processing URL news:', error);
        // Error already handled by apiRequest
    } finally {
        hideButtonLoading(button, originalButtonText);
    }
}

// Process file news to extract entities and relations
async function processFileNews() {
    const form = document.getElementById('file-form');
    const button = form.querySelector('button[type="submit"]');
    const originalButtonText = button.textContent;
    const resultContainer = document.getElementById('file-result');
    
    try {
        showButtonLoading(button, 'Processing...');
        resultContainer.innerHTML = '<div class="loading-container"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>';
        
        const formData = new FormData(form);
        const file = formData.get('file');
        
        if (!file || file.size === 0) {
            showAlert('error', 'Please select a file to process');
            return;
        }
        
        const data = {
            file: file
        };
        
        const result = await apiRequest('/api/v1/autokg/process-news', 'POST', data);
        
        // Render the file processing result
        renderProcessingResult(result, resultContainer);
        
    } catch (error) {
        console.error('Error processing file news:', error);
        // Error already handled by apiRequest
    } finally {
        hideButtonLoading(button, originalButtonText);
    }
}

// Render extraction result
function renderExtractionResult(result, container) {
    if (!result || (!result.entities && !result.relations)) {
        container.innerHTML = '<div class="alert alert-warning">No entities or relations extracted</div>';
        return;
    }
    
    const html = `
        <div class="card">
            <div class="card-body">
                <h5 class="card-title mb-4">Extraction Results</h5>
                
                ${result.entities && result.entities.length > 0 ? `
                    <div class="mb-4">
                        <h6 class="text-primary">Entities (${result.entities.length})</h6>
                        <div class="row">
                            ${result.entities.map((entity, index) => `
                                <div class="col-md-6 mb-2">
                                    <span class="badge bg-primary me-1">${index + 1}</span>
                                    <span class="entity-name">${entity.name}</span>
                                    <span class="badge bg-secondary">${entity.type}</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}
                
                ${result.relations && result.relations.length > 0 ? `
                    <div class="mb-4">
                        <h6 class="text-success">Relations (${result.relations.length})</h6>
                        <div class="row">
                            ${result.relations.map((relation, index) => `
                                <div class="col-md-12 mb-2">
                                    <span class="badge bg-success me-1">${index + 1}</span>
                                    <span class="entity-name">${relation.head_entity}</span> → 
                                    <span class="relation-type">${relation.relation_type}</span> → 
                                    <span class="entity-name">${relation.tail_entity}</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}
            </div>
        </div>
    `;
    
    container.innerHTML = html;
}

// Render processing result
function renderProcessingResult(result, container) {
    if (!result || (!result.entities && !result.relations)) {
        container.innerHTML = '<div class="alert alert-warning">No entities or relations extracted</div>';
        return;
    }
    
    const html = `
        <div class="card">
            <div class="card-body">
                <h5 class="card-title mb-4">Processing Results</h5>
                
                <div class="row">
                    <div class="col-md-6">
                        ${result.entities && result.entities.length > 0 ? `
                            <div class="mb-4">
                                <h6 class="text-primary">Entities (${result.entities.length})</h6>
                                <div class="list-group">
                                    ${result.entities.map((entity, index) => `
                                        <div class="list-group-item list-group-item-action">
                                            <div class="fw-bold">${entity.name}</div>
                                            <div class="text-sm text-muted">${entity.type}</div>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                        ` : ''}
                    </div>
                    <div class="col-md-6">
                        ${result.relations && result.relations.length > 0 ? `
                            <div class="mb-4">
                                <h6 class="text-success">Relations (${result.relations.length})</h6>
                                <div class="list-group">
                                    ${result.relations.map((relation, index) => `
                                        <div class="list-group-item list-group-item-action">
                                            <div class="fw-bold">${relation.relation_type}</div>
                                            <div class="text-sm">
                                                <span class="text-primary">${relation.head_entity_name}</span> → 
                                                <span class="text-primary">${relation.tail_entity_name}</span>
                                            </div>
                                            ${relation.head_entity_type && relation.tail_entity_type ? `
                                                <div class="text-xs text-muted mt-1">
                                                    ${relation.head_entity_type} → ${relation.tail_entity_type}
                                                </div>
                                            ` : ''}
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                        ` : ''}
                    </div>
                </div>
                
                ${result.summary ? `
                    <div class="mt-4">
                        <h6 class="text-info">Summary</h6>
                        <p class="text-muted">${result.summary}</p>
                    </div>
                ` : ''}
            </div>
        </div>
    `;
    
    container.innerHTML = html;
}

// Initialize the page when it's loaded
window.initAutoKGPage = initAutoKGPage;
