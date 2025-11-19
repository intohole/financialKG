// Relation Management JavaScript

// Initialize the relation management page
function initRelationPage() {
    console.log('Relation Management page initialized');
    
    // Set up event listeners
    setupRelationEventListeners();
    
    // Load relations by default
    fetchRelations();
}

// Set up event listeners for relation management
function setupRelationEventListeners() {
    // Form submission for creating a new relation
    const createRelationForm = document.getElementById('create-relation-form');
    if (createRelationForm) {
        createRelationForm.addEventListener('submit', (e) => {
            e.preventDefault();
            createRelation();
        });
    }
    
    // Search button event listener
    const searchRelationBtn = document.getElementById('search-relation-btn');
    if (searchRelationBtn) {
        searchRelationBtn.addEventListener('click', () => {
            fetchRelations();
        });
    }
    
    // Search input enter key event listener
    const searchRelationInput = document.getElementById('search-relation-input');
    if (searchRelationInput) {
        searchRelationInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                fetchRelations();
            }
        });
    }
}

// Create a new relation
async function createRelation() {
    const form = document.getElementById('create-relation-form');
    const button = form.querySelector('button[type="submit"]');
    const originalButtonText = button.textContent;
    
    try {
        showButtonLoading(button, 'Creating...');
        
        const formData = new FormData(form);
        const relationData = {
            source_entity_id: formData.get('source_entity_id'),
            target_entity_id: formData.get('target_entity_id'),
            type: formData.get('type'),
            properties: {}
        };
        
        // Extract properties
        const propertyInputs = form.querySelectorAll('.relation-property-input');
        propertyInputs.forEach(input => {
            const key = input.getAttribute('data-key');
            const value = input.value;
            if (key && value) {
                relationData.properties[key] = value;
            }
        });
        
        const response = await apiRequest('/api/v1/relations/', 'POST', relationData);
        
        showAlert('success', `Relation created successfully: ${response.type}`);
        
        // Reset the form
        form.reset();
        
        // Load updated relations
        fetchRelations();
        
    } catch (error) {
        console.error('Error creating relation:', error);
        // Error already handled by apiRequest
    } finally {
        hideButtonLoading(button, originalButtonText);
    }
}

// Fetch relations from the API
async function fetchRelations() {
    const relationsContainer = document.getElementById('relations-container');
    const searchInput = document.getElementById('search-relation-input');
    const searchQuery = searchInput ? searchInput.value.trim() : '';
    
    // Show loading state in relations container
    relationsContainer.innerHTML = `
        <div class="card">
            <div class="card-body p-0">
                <table class="table table-hover m-0">
                    <tbody>
                        <tr><td colspan="7" class="text-center"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div> 加载中...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    `;
    
    try {
        let url = '/api/v1/relations/?limit=100';
        if (searchQuery) {
            url += `&search=${encodeURIComponent(searchQuery)}`;
        }
        
        const relations = await apiRequest(url, 'GET');
        
        // Render relations
        renderRelations(relations);
        
    } catch (error) {
        console.error('Error fetching relations:', error);
        // Show error message in relations container
        relationsContainer.innerHTML = `
            <div class="card">
                <div class="card-body p-0">
                    <table class="table table-hover m-0">
                        <tbody>
                            <tr><td colspan="7" class="text-center text-danger">加载失败，请稍后重试</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        `;
        // Show alert for error
        showAlert('error', '获取关系失败: ' + error.message);
    }
}

// Render relations in the table
function renderRelations(relations) {
    const relationsContainer = document.getElementById('relations-container');
    
    if (!relations || relations.length === 0) {
        relationsContainer.innerHTML = `
            <div class="card">
                <div class="card-body text-center py-5">
                    <p class="text-muted">No relations found</p>
                    <button class="btn btn-primary" onclick="fetchRelations()">
                        <i class="fas fa-sync"></i> Refresh
                    </button>
                </div>
            </div>
        `;
        return;
    }
    
    // Create table HTML
    const tableHtml = `
        <div class="card">
            <div class="card-body p-0">
                <table class="table table-hover m-0">
                    <thead>
                        <tr>
                            <th>Source Entity</th>
                            <th>Target Entity</th>
                            <th>Type</th>
                            <th>Properties</th>
                            <th>Created At</th>
                            <th>Updated At</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${relations.map(relation => `
                            <tr>
                                <td>${relation.source_entity.name || relation.source_entity_id}</td>
                                <td>${relation.target_entity.name || relation.target_entity_id}</td>
                                <td>${relation.type}</td>
                                <td>
                                    ${Object.keys(relation.properties).slice(0, 3).map(key => `${key}: ${relation.properties[key]}`).join(', ')}
                                    ${Object.keys(relation.properties).length > 3 ? `... (${Object.keys(relation.properties).length} total)` : ''}
                                </td>
                                <td>${formatDate(relation.created_at)}</td>
                                <td>${formatDate(relation.updated_at)}</td>
                                <td>
                                    <button class="btn btn-sm btn-info me-1" onclick="viewRelation('${relation.id}')">
                                        <i class="fas fa-eye"></i>
                                    </button>
                                    <button class="btn btn-sm btn-warning me-1" onclick="editRelation('${relation.id}')">
                                        <i class="fas fa-edit"></i>
                                    </button>
                                    <button class="btn btn-sm btn-danger btn-delete" data-url="/api/v1/relations/${relation.id}/" data-name="${relation.type}">
                                        <i class="fas fa-trash"></i>
                                    </button>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        </div>
    `;
    
    relationsContainer.innerHTML = tableHtml;
}

// View relation details
async function viewRelation(relationId) {
    try {
        const relation = await apiRequest(`/api/v1/relations/${relationId}/`, 'GET');
        
        // Create modal content
        const modalHtml = `
            <div class="modal fade" id="viewRelationModal" tabindex="-1" aria-labelledby="viewRelationModalLabel" aria-hidden="true">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="viewRelationModalLabel">Relation Details</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <div class="mb-3">
                                <strong>ID:</strong> ${relation.id}
                            </div>
                            <div class="mb-3">
                                <strong>Source Entity:</strong> ${relation.source_entity ? `${relation.source_entity.name} (${relation.source_entity_id})` : relation.source_entity_id}
                            </div>
                            <div class="mb-3">
                                <strong>Target Entity:</strong> ${relation.target_entity ? `${relation.target_entity.name} (${relation.target_entity_id})` : relation.target_entity_id}
                            </div>
                            <div class="mb-3">
                                <strong>Type:</strong> ${relation.type}
                            </div>
                            <div class="mb-3">
                                <strong>Properties:</strong>
                                <pre>${formatJson(relation.properties)}</pre>
                            </div>
                            <div class="mb-3">
                                <strong>Created At:</strong> ${formatDate(relation.created_at)}
                            </div>
                            <div class="mb-3">
                                <strong>Updated At:</strong> ${formatDate(relation.updated_at)}
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Insert modal into the DOM
        const body = document.querySelector('body');
        body.innerHTML += modalHtml;
        
        // Show the modal
        const modal = new bootstrap.Modal(document.getElementById('viewRelationModal'));
        modal.show();
        
        // Remove modal from DOM after it's hidden
        const modalElement = document.getElementById('viewRelationModal');
        modalElement.addEventListener('hidden.bs.modal', () => {
            modalElement.remove();
        });
        
    } catch (error) {
        console.error('Error viewing relation:', error);
        // Error already handled by apiRequest
    }
}

// Edit relation
async function editRelation(relationId) {
    try {
        const relation = await apiRequest(`/relations/${relationId}/`, 'GET');
        
        // Create edit form
        const modalHtml = `
            <div class="modal fade" id="editRelationModal" tabindex="-1" aria-labelledby="editRelationModalLabel" aria-hidden="true">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="editRelationModalLabel">Edit Relation</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <form id="edit-relation-form">
                                <div class="mb-3">
                                    <label for="edit-relation-id" class="form-label">ID</label>
                                    <input type="text" class="form-control" id="edit-relation-id" value="${relation.id}" readonly>
                                </div>
                                <div class="mb-3">
                                    <label for="edit-relation-source" class="form-label">Source Entity ID</label>
                                    <input type="text" class="form-control" id="edit-relation-source" value="${relation.source_entity_id}" required>
                                </div>
                                <div class="mb-3">
                                    <label for="edit-relation-target" class="form-label">Target Entity ID</label>
                                    <input type="text" class="form-control" id="edit-relation-target" value="${relation.target_entity_id}" required>
                                </div>
                                <div class="mb-3">
                                    <label for="edit-relation-type" class="form-label">Type</label>
                                    <input type="text" class="form-control" id="edit-relation-type" value="${relation.type}" required>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Properties</label>
                                    <div id="edit-relation-properties-container">
                                        ${Object.keys(relation.properties).map(key => `
                                            <div class="input-group mb-2">
                                                <input type="text" class="form-control" value="${key}" readonly>
                                                <input type="text" class="form-control" value="${relation.properties[key]}" data-key="${key}">
                                            </div>
                                        `).join('')}
                                    </div>
                                </div>
                                <div class="d-flex justify-content-end">
                                    <button type="submit" class="btn btn-primary">Save Changes</button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Insert modal into the DOM
        const body = document.querySelector('body');
        body.innerHTML += modalHtml;
        
        // Show the modal
        const modal = new bootstrap.Modal(document.getElementById('editRelationModal'));
        modal.show();
        
        // Set up form submission
        const form = document.getElementById('edit-relation-form');
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const button = form.querySelector('button[type="submit"]');
            const originalButtonText = button.textContent;
            
            try {
                showButtonLoading(button, 'Saving...');
                
                const updatedRelation = {
                    source_entity_id: document.getElementById('edit-relation-source').value,
                    target_entity_id: document.getElementById('edit-relation-target').value,
                    type: document.getElementById('edit-relation-type').value,
                    properties: {}
                };
                
                const propertyInputs = document.querySelectorAll('#edit-relation-properties-container input[data-key]');
                propertyInputs.forEach(input => {
                    const key = input.getAttribute('data-key');
                    const value = input.value;
                    if (key && value) {
                        updatedRelation.properties[key] = value;
                    }
                });
                
                await apiRequest(`/api/v1/relations/${relationId}/`, 'PUT', updatedRelation);
                
                showAlert('success', 'Relation updated successfully');
                
                // Close the modal
                modal.hide();
                
                // Reload relations
                fetchRelations();
                
            } catch (error) {
                console.error('Error updating relation:', error);
                // Error already handled by apiRequest
            } finally {
                hideButtonLoading(button, originalButtonText);
            }
        });
        
        // Remove modal from DOM after it's hidden
        const modalElement = document.getElementById('editRelationModal');
        modalElement.addEventListener('hidden.bs.modal', () => {
            modalElement.remove();
        });
        
    } catch (error) {
        console.error('Error editing relation:', error);
        // Error already handled by apiRequest
    }
}

// Initialize the page when it's loaded
window.initRelationPage = initRelationPage;
