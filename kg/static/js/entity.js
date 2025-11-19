// Entity Management JavaScript

// Initialize the entity management page
function initEntityPage() {
    console.log('Entity Management page initialized');
    
    // Set up event listeners
    setupEntityEventListeners();
    
    // Load entities by default
    fetchEntities();
}

// Set up event listeners for entity management
function setupEntityEventListeners() {
    // Form submission for creating a new entity
    const createEntityForm = document.getElementById('create-entity-form');
    if (createEntityForm) {
        createEntityForm.addEventListener('submit', (e) => {
            e.preventDefault();
            createEntity();
        });
    }
    
    // Search button event listener
    const searchEntityBtn = document.getElementById('search-entity-btn');
    if (searchEntityBtn) {
        searchEntityBtn.addEventListener('click', () => {
            fetchEntities();
        });
    }
    
    // Search input enter key event listener
    const searchEntityInput = document.getElementById('search-entity-input');
    if (searchEntityInput) {
        searchEntityInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                fetchEntities();
            }
        });
    }
}

// Create a new entity
async function createEntity() {
    const form = document.getElementById('create-entity-form');
    const button = form.querySelector('button[type="submit"]');
    const originalButtonText = button.textContent;
    
    try {
        showButtonLoading(button, 'Creating...');
        
        const formData = new FormData(form);
        const entityData = {
            type: formData.get('type'),
            name: formData.get('name'),
            properties: {}
        };
        
        // Extract properties
        const propertyInputs = form.querySelectorAll('.entity-property-input');
        propertyInputs.forEach(input => {
            const key = input.getAttribute('data-key');
            const value = input.value;
            if (key && value) {
                entityData.properties[key] = value;
            }
        });
        
        const response = await apiRequest('/api/v1/entities/', 'POST', entityData);
        
        showAlert('success', `Entity created successfully: ${response.name}`);
        
        // Reset the form
        form.reset();
        
        // Load updated entities
        fetchEntities();
        
    } catch (error) {
        console.error('Error creating entity:', error);
        // Error already handled by apiRequest
    } finally {
        hideButtonLoading(button, originalButtonText);
    }
}

// Fetch entities from the API
async function fetchEntities(page = 1, pageSize = 100) {
    const entitiesContainer = document.getElementById('entities-container');
    const paginationContainer = document.getElementById('pagination-container');
    const searchInput = document.getElementById('search-entity-input');
    const searchQuery = searchInput ? searchInput.value.trim() : '';
    
    try {
        // Show loading state
        entitiesContainer.innerHTML = '<div class="card"><div class="card-body p-0"><table class="table table-hover m-0"><tbody><tr><td colspan="6" class="text-center"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div> 加载中...</td></tr></tbody></table></div></div>';
        paginationContainer.innerHTML = '';
        
        let url = `/api/v1/entities/?page=${page}&page_size=${pageSize}`;
        if (searchQuery) {
            url += `&search=${encodeURIComponent(searchQuery)}`;
        }
        
        const response = await apiRequest(url, 'GET');
        const paginationData = response.data;
        
        // Render entities
        renderEntities(paginationData.items);
        
        // Render pagination
        renderPagination(paginationData);
        
    } catch (error) {
        console.error('Error fetching entities:', error);
        entitiesContainer.innerHTML = '<div class="card"><div class="card-body text-center py-5"><p class="text-danger">获取实体失败，请稍后重试</p><button class="btn btn-primary" onclick="fetchEntities()"><i class="fas fa-sync"></i> 刷新</button></div></div>';
        paginationContainer.innerHTML = '';
        // Error already handled by apiRequest
    }
}

// Render entities in the table
function renderEntities(entities) {
    const entitiesContainer = document.getElementById('entities-container');
    
    if (!entities || entities.length === 0) {
        entitiesContainer.innerHTML = `
            <div class="card">
                <div class="card-body text-center py-5">
                    <p class="text-muted">No entities found</p>
                    <button class="btn btn-primary" onclick="fetchEntities()">
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
                            <th>Name</th>
                            <th>Type</th>
                            <th>Properties</th>
                            <th>Created At</th>
                            <th>Updated At</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${entities.map(entity => `
                            <tr>
                                <td>${entity.name}</td>
                                <td>${entity.type}</td>
                                <td>
                                    ${Object.keys(entity.properties).slice(0, 3).map(key => `${key}: ${entity.properties[key]}`).join(', ')}
                                    ${Object.keys(entity.properties).length > 3 ? `... (${Object.keys(entity.properties).length} total)` : ''}
                                </td>
                                <td>${formatDate(entity.created_at)}</td>
                                <td>${formatDate(entity.updated_at)}</td>
                                <td>
                                    <button class="btn btn-sm btn-info me-1" onclick="viewEntity('${entity.id}')">
                                        <i class="fas fa-eye"></i>
                                    </button>
                                    <button class="btn btn-sm btn-warning me-1" onclick="editEntity('${entity.id}')">
                                        <i class="fas fa-edit"></i>
                                    </button>
                                    <button class="btn btn-sm btn-danger btn-delete" data-url="/api/v1/entities/${entity.id}/" data-name="${entity.name}">
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
    
    entitiesContainer.innerHTML = tableHtml;
}

// Render pagination controls
function renderPagination(paginationData) {
    const paginationContainer = document.getElementById('pagination-container');
    if (!paginationContainer) return;
    
    const { total, page, size, total_pages } = paginationData;
    
    // Create pagination HTML
    const paginationHtml = `
        <nav aria-label="Entity pagination">
            <ul class="pagination justify-content-center">
                <!-- Previous Page Button -->
                <li class="page-item ${page === 1 ? 'disabled' : ''}">
                    <button class="page-link" onclick="fetchEntities(${page - 1}, ${size})" aria-label="Previous">
                        <span aria-hidden="true">&laquo;</span>
                    </button>
                </li>
                
                <!-- Page Buttons -->
                ${Array.from({ length: total_pages }, (_, i) => i + 1)
                    .map(pageNumber => `
                        <li class="page-item ${page === pageNumber ? 'active' : ''}">
                            <button class="page-link" onclick="fetchEntities(${pageNumber}, ${size})">
                                ${pageNumber}
                            </button>
                        </li>
                    `).join('')}
                
                <!-- Next Page Button -->
                <li class="page-item ${page === total_pages ? 'disabled' : ''}">
                    <button class="page-link" onclick="fetchEntities(${page + 1}, ${size})" aria-label="Next">
                        <span aria-hidden="true">&raquo;</span>
                    </button>
                </li>
            </ul>
            <div class="text-center mt-2">
                <small>显示第 ${page} 页，共 ${total_pages} 页，总计 ${total} 条记录</small>
            </div>
        </nav>
    `;
    
    paginationContainer.innerHTML = paginationHtml;
}

// View entity details
async function viewEntity(entityId) {
    try {
        const entity = await apiRequest(`/api/v1/entities/${entityId}/`, 'GET');
        
        // Create modal content
        const modalHtml = `
            <div class="modal fade" id="viewEntityModal" tabindex="-1" aria-labelledby="viewEntityModalLabel" aria-hidden="true">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="viewEntityModalLabel">Entity Details</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <div class="mb-3">
                                <strong>ID:</strong> ${entity.id}
                            </div>
                            <div class="mb-3">
                                <strong>Name:</strong> ${entity.name}
                            </div>
                            <div class="mb-3">
                                <strong>Type:</strong> ${entity.type}
                            </div>
                            <div class="mb-3">
                                <strong>Properties:</strong>
                                <pre>${formatJson(entity.properties)}</pre>
                            </div>
                            <div class="mb-3">
                                <strong>Created At:</strong> ${formatDate(entity.created_at)}
                            </div>
                            <div class="mb-3">
                                <strong>Updated At:</strong> ${formatDate(entity.updated_at)}
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
        const modal = new bootstrap.Modal(document.getElementById('viewEntityModal'));
        modal.show();
        
        // Remove modal from DOM after it's hidden
        const modalElement = document.getElementById('viewEntityModal');
        modalElement.addEventListener('hidden.bs.modal', () => {
            modalElement.remove();
        });
        
    } catch (error) {
        console.error('Error viewing entity:', error);
        // Error already handled by apiRequest
    }
}

// Edit entity
async function editEntity(entityId) {
    try {
        const entity = await apiRequest(`/api/v1/entities/${entityId}/`, 'GET');
        
        // Create edit form
        const modalHtml = `
            <div class="modal fade" id="editEntityModal" tabindex="-1" aria-labelledby="editEntityModalLabel" aria-hidden="true">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="editEntityModalLabel">Edit Entity</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <form id="edit-entity-form">
                                <div class="mb-3">
                                    <label for="edit-entity-id" class="form-label">ID</label>
                                    <input type="text" class="form-control" id="edit-entity-id" value="${entity.id}" readonly>
                                </div>
                                <div class="mb-3">
                                    <label for="edit-entity-name" class="form-label">Name</label>
                                    <input type="text" class="form-control" id="edit-entity-name" value="${entity.name}" required>
                                </div>
                                <div class="mb-3">
                                    <label for="edit-entity-type" class="form-label">Type</label>
                                    <input type="text" class="form-control" id="edit-entity-type" value="${entity.type}" required>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Properties</label>
                                    <div id="edit-properties-container">
                                        ${Object.keys(entity.properties).map(key => `
                                            <div class="input-group mb-2">
                                                <input type="text" class="form-control" value="${key}" readonly>
                                                <input type="text" class="form-control" value="${entity.properties[key]}" data-key="${key}">
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
        const modal = new bootstrap.Modal(document.getElementById('editEntityModal'));
        modal.show();
        
        // Set up form submission
        const form = document.getElementById('edit-entity-form');
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const button = form.querySelector('button[type="submit"]');
            const originalButtonText = button.textContent;
            
            try {
                showButtonLoading(button, 'Saving...');
                
                const updatedEntity = {
                    name: document.getElementById('edit-entity-name').value,
                    type: document.getElementById('edit-entity-type').value,
                    properties: {}
                };
                
                const propertyInputs = document.querySelectorAll('#edit-properties-container input[data-key]');
                propertyInputs.forEach(input => {
                    const key = input.getAttribute('data-key');
                    const value = input.value;
                    if (key && value) {
                        updatedEntity.properties[key] = value;
                    }
                });
                
                await apiRequest(`/api/v1/entities/${entityId}/`, 'PUT', updatedEntity);
                
                showAlert('success', 'Entity updated successfully');
                
                // Close the modal
                modal.hide();
                
                // Reload entities
                fetchEntities();
                
            } catch (error) {
                console.error('Error updating entity:', error);
                // Error already handled by apiRequest
            } finally {
                hideButtonLoading(button, originalButtonText);
            }
        });
        
        // Remove modal from DOM after it's hidden
        const modalElement = document.getElementById('editEntityModal');
        modalElement.addEventListener('hidden.bs.modal', () => {
            modalElement.remove();
        });
        
    } catch (error) {
        console.error('Error editing entity:', error);
        // Error already handled by apiRequest
    }
}

// Initialize the page when it's loaded
window.initEntityPage = initEntityPage;