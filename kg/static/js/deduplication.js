// Deduplication JavaScript

// Initialize the Deduplication page
function initDeduplicationPage() {
    console.log('Deduplication page initialized');
    
    // Set up event listeners
    setupDeduplicationEvents();
}

// Set up event listeners for Deduplication functions
function setupDeduplicationEvents() {
    // Entity Deduplication form
    const entityDedupForm = document.getElementById('entity-dedup-form');
    if (entityDedupForm) {
        entityDedupForm.addEventListener('submit', (e) => {
            e.preventDefault();
            entityDeduplication();
        });
    }
    
    // Relation Deduplication form
    const relationDedupForm = document.getElementById('relation-dedup-form');
    if (relationDedupForm) {
        relationDedupForm.addEventListener('submit', (e) => {
            e.preventDefault();
            relationDeduplication();
        });
    }
    
    // Entity Merge form
    const entityMergeForm = document.getElementById('entity-merge-form');
    if (entityMergeForm) {
        entityMergeForm.addEventListener('submit', (e) => {
            e.preventDefault();
            mergeEntities();
        });
    }
    
    // Relation Merge form
    const relationMergeForm = document.getElementById('relation-merge-form');
    if (relationMergeForm) {
        relationMergeForm.addEventListener('submit', (e) => {
            e.preventDefault();
            mergeRelations();
        });
    }
}

// Perform entity deduplication
async function entityDeduplication() {
    const form = document.getElementById('entity-dedup-form');
    const button = form.querySelector('button[type="submit"]');
    const originalButtonText = button.textContent;
    const resultContainer = document.getElementById('entity-dedup-result');
    
    try {
        showButtonLoading(button, 'Deduplicating...');
        resultContainer.innerHTML = '<div class="loading-container"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>';
        
        const formData = new FormData(form);
        const data = {
            method: formData.get('method'),
            threshold: parseFloat(formData.get('threshold')) || 0.8,
            type: formData.get('type') || '',
            limit: parseInt(formData.get('limit')) || 10
        };
        
        // 调用实体去重API
        const result = await apiRequest('/api/v1/deduplication/run', 'POST', data);
        
        // Render the entity deduplication result
        renderEntityDedupResult(result, resultContainer);
        
    } catch (error) {
        console.error('Error in entity deduplication:', error);
        // Error already handled by apiRequest
    } finally {
        hideButtonLoading(button, originalButtonText);
    }
}

// Perform relation deduplication
async function relationDeduplication() {
    const form = document.getElementById('relation-dedup-form');
    const button = form.querySelector('button[type="submit"]');
    const originalButtonText = button.textContent;
    const resultContainer = document.getElementById('relation-dedup-result');
    
    try {
        showButtonLoading(button, 'Deduplicating...');
        resultContainer.innerHTML = '<div class="loading-container"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>';
        
        const formData = new FormData(form);
        const data = {
            method: formData.get('method'),
            threshold: parseFloat(formData.get('threshold')) || 0.8,
            type: formData.get('type') || '',
            limit: parseInt(formData.get('limit')) || 10
        };
        
        // 调用关系去重API
        const result = await apiRequest('/api/v1/deduplication/run', 'POST', {type: 'relations'});
        
        // Render the relation deduplication result
        renderRelationDedupResult(result, resultContainer);
        
    } catch (error) {
        console.error('Error in relation deduplication:', error);
        // Error already handled by apiRequest
    } finally {
        hideButtonLoading(button, originalButtonText);
    }
}

// Merge entities
async function mergeEntities() {
    const form = document.getElementById('entity-merge-form');
    const button = form.querySelector('button[type="submit"]');
    const originalButtonText = button.textContent;
    const resultContainer = document.getElementById('entity-merge-result');
    
    try {
        showButtonLoading(button, 'Merging...');
        resultContainer.innerHTML = '<div class="loading-container"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>';
        
        const formData = new FormData(form);
        const data = {
            entity_ids: formData.getAll('entity_ids[]'),
            keep_id: formData.get('keep_id') || ''
        };
        
        // Validate data
        if (!data.entity_ids || data.entity_ids.length < 2) {
            showAlert('error', 'Please select at least two entities to merge');
            return;
        }
        
        // 调用实体合并API（通过去重路由处理）
        const result = await apiRequest('/api/v1/deduplication/run', 'POST', {type: 'entities', action: 'merge', merge_groups: data});
        
        // Render the merge result
        renderMergeResult(result, resultContainer, 'entities');
        
    } catch (error) {
        console.error('Error in merging entities:', error);
        // Error already handled by apiRequest
    } finally {
        hideButtonLoading(button, originalButtonText);
    }
}

// Merge relations
async function mergeRelations() {
    const form = document.getElementById('relation-merge-form');
    const button = form.querySelector('button[type="submit"]');
    const originalButtonText = button.textContent;
    const resultContainer = document.getElementById('relation-merge-result');
    
    try {
        showButtonLoading(button, 'Merging...');
        resultContainer.innerHTML = '<div class="loading-container"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>';
        
        const formData = new FormData(form);
        const data = {
            relation_ids: formData.getAll('relation_ids[]'),
            keep_id: formData.get('keep_id') || ''
        };
        
        // Validate data
        if (!data.relation_ids || data.relation_ids.length < 2) {
            showAlert('error', 'Please select at least two relations to merge');
            return;
        }
        
        // 调用关系合并API（通过去重路由处理）
        const result = await apiRequest('/api/v1/deduplication/run', 'POST', {type: 'relations', action: 'merge', merge_groups: data});
        
        // Render the merge result
        renderMergeResult(result, resultContainer, 'relations');
        
    } catch (error) {
        console.error('Error in merging relations:', error);
        // Error already handled by apiRequest
    } finally {
        hideButtonLoading(button, originalButtonText);
    }
}

// Render entity deduplication result
function renderEntityDedupResult(result, container) {
    if (!result || !result.duplicate_groups || result.duplicate_groups.length === 0) {
        container.innerHTML = '<div class="alert alert-success">No duplicate entities found</div>';
        return;
    }
    
    const html = `
        <div class="card">
            <div class="card-body">
                <h5 class="card-title mb-4">Entity Duplicate Groups (${result.duplicate_groups.length})</h5>
                
                ${result.duplicate_groups.map((group, groupIndex) => `
                    <div class="mb-4 border-bottom pb-3">
                        <h6 class="text-primary mb-3">Group ${groupIndex + 1} (${group.entities.length} entities)</h6>
                        <div class="table-responsive">
                            <table class="table table-sm table-bordered">
                                <thead>
                                    <tr>
                                        <th>Select</th>
                                        <th>ID</th>
                                        <th>Name</th>
                                        <th>Type</th>
                                        <th>Description</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${group.entities.map(entity => `
                                        <tr>
                                            <td><input type="checkbox" name="entity_ids[]" value="${entity.id}" class="form-check-input"></td>
                                            <td>${entity.id}</td>
                                            <td>${entity.name}</td>
                                            <td>${entity.type}</td>
                                            <td>${entity.description || '-'}</td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                    </div>
                `).join('')}
                
                <div class="mt-4">
                    <button type="button" class="btn btn-danger me-2" onclick="document.getElementById('entity-merge-modal').showModal()">Merge Selected Entities</button>
                    <button type="button" class="btn btn-secondary" onclick="document.querySelectorAll('input[name="entity_ids[]"]').forEach(cb => cb.checked = false)">Clear Selection</button>
                </div>
            </div>
        </div>
    `;
    
    container.innerHTML = html;
}

// Render relation deduplication result
function renderRelationDedupResult(result, container) {
    if (!result || !result.duplicate_groups || result.duplicate_groups.length === 0) {
        container.innerHTML = '<div class="alert alert-success">No duplicate relations found</div>';
        return;
    }
    
    const html = `
        <div class="card">
            <div class="card-body">
                <h5 class="card-title mb-4">Relation Duplicate Groups (${result.duplicate_groups.length})</h5>
                
                ${result.duplicate_groups.map((group, groupIndex) => `
                    <div class="mb-4 border-bottom pb-3">
                        <h6 class="text-primary mb-3">Group ${groupIndex + 1} (${group.relations.length} relations)</h6>
                        <div class="table-responsive">
                            <table class="table table-sm table-bordered">
                                <thead>
                                    <tr>
                                        <th>Select</th>
                                        <th>ID</th>
                                        <th>Head Entity</th>
                                        <th>Relation Type</th>
                                        <th>Tail Entity</th>
                                        <th>Description</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${group.relations.map(relation => `
                                        <tr>
                                            <td><input type="checkbox" name="relation_ids[]" value="${relation.id}" class="form-check-input"></td>
                                            <td>${relation.id}</td>
                                            <td>${relation.head_entity_name} (ID: ${relation.head_entity})</td>
                                            <td>${relation.relation_type}</td>
                                            <td>${relation.tail_entity_name} (ID: ${relation.tail_entity})</td>
                                            <td>${relation.description || '-'}</td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                    </div>
                `).join('')}
                
                <div class="mt-4">
                    <button type="button" class="btn btn-danger me-2" onclick="document.getElementById('relation-merge-modal').showModal()">Merge Selected Relations</button>
                    <button type="button" class="btn btn-secondary" onclick="document.querySelectorAll('input[name="relation_ids[]"]').forEach(cb => cb.checked = false)">Clear Selection</button>
                </div>
            </div>
        </div>
    `;
    
    container.innerHTML = html;
}

// Render merge result
function renderMergeResult(result, container, type) {
    if (!result || !result.success) {
        container.innerHTML = `<div class="alert alert-danger">Failed to merge ${type}</div>`;
        return;
    }
    
    const html = `
        <div class="alert alert-success">
            <strong>Success!</strong> Merged ${type} into a single ${type.slice(0, -1)}.
            ${result.message ? `<br><em>${result.message}</em>` : ''}
        </div>
    `;
    
    container.innerHTML = html;
}

// Initialize the page when it's loaded
window.initDeduplicationPage = initDeduplicationPage;
