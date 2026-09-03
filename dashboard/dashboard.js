// API Configuration
const API_URL = '';
// For local testing, uncomment this:
// const API_URL = 'http://localhost:8000';
let allLeads = [];
let filteredLeads = [];

// Load leads from API
async function loadLeads() {
    try {
        const response = await fetch(`${API_URL}/leads`);
        const data = await response.json();
        
        // Convert object to array
        allLeads = Object.values(data.leads || {});
        
        // Update stats
        updateStats(allLeads);
        
        // Render leads
        renderLeads(allLeads);
        
        // Update timestamp
        document.getElementById('lastUpdated').textContent = 
            `Last updated: ${new Date().toLocaleTimeString()}`;
            
    } catch (error) {
        console.error('Error loading leads:', error);
        document.getElementById('leadsList').innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">⚠️</div>
                <h3>Could not load leads</h3>
                <p>Make sure the backend server is running on ${API_URL}</p>
                <button onclick="loadLeads()" style="margin-top:12px;padding:8px 16px;background:#3b82f6;color:white;border:none;border-radius:6px;cursor:pointer;">
                    Try Again
                </button>
            </div>
        `;
    }
}

// Update stats
async function updateStats(leads) {
    // Try to get stats from API
    try {
        const response = await fetch(`${API_URL}/leads/stats`);
        const stats = await response.json();
        
        document.getElementById('totalLeads').textContent = stats.total || 0;
        document.getElementById('hotLeads').textContent = stats.hot || 0;
        document.getElementById('warmLeads').textContent = stats.warm || 0;
        document.getElementById('coldLeads').textContent = stats.cold || 0;
        document.getElementById('lowLeads').textContent = stats.low || 0;
    } catch (error) {
        // Fallback: calculate from leads array
        const total = leads.length;
        const hot = leads.filter(l => l.score?.priority === 'HOT').length;
        const warm = leads.filter(l => l.score?.priority === 'WARM').length;
        const cold = leads.filter(l => l.score?.priority === 'COLD').length;
        const low = leads.filter(l => l.score?.priority === 'LOW').length;
        
        document.getElementById('totalLeads').textContent = total;
        document.getElementById('hotLeads').textContent = hot;
        document.getElementById('warmLeads').textContent = warm;
        document.getElementById('coldLeads').textContent = cold;
        document.getElementById('lowLeads').textContent = low;
    }
}

// Render leads
function renderLeads(leads) {
    const container = document.getElementById('leadsList');
    
    if (leads.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">🤖</div>
                <h3>No leads yet</h3>
                <p>Start a conversation with the chat widget to capture leads.</p>
            </div>
        `;
        return;
    }
    
    // Sort by score (highest first)
    const sorted = [...leads].sort((a, b) => 
        (b.score?.score || 0) - (a.score?.score || 0)
    );
    
    container.innerHTML = sorted.map(lead => {
        const priority = lead.score?.priority || 'LOW';
        const priorityClass = priority.toLowerCase();
        const score = lead.score?.score || 0;
        const data = lead.data || {};
        
        return `
            <div class="lead-item" onclick="viewLead('${lead.conversation_id}')">
                <div class="lead-info">
                    <div class="lead-name">
                        ${data.name || 'Unknown Customer'}
                    </div>
                    <div class="lead-details">
                        <span>📍 ${data.location || 'No location'}</span>
                        <span>🏠 ${data.property_type || 'No property'}</span>
                        <span>💰 ${data.budget || 'No budget'}</span>
                        <span>📱 ${data.phone ? '✅ Contact' : '❌ No contact'}</span>
                    </div>
                </div>
                <div class="lead-score">
                    <span class="priority-badge ${priorityClass}">
                        ${getPriorityIcon(priority)} ${priority}
                    </span>
                    <span class="lead-score-number">${score}/100</span>
                    <div class="lead-actions">
                        <button class="btn-action btn-view" onclick="event.stopPropagation();viewLead('${lead.conversation_id}')">
                            👁️ View
                        </button>
                        ${data.phone ? `
                            <button class="btn-action btn-call" onclick="event.stopPropagation();window.location.href='tel:${data.phone}'">
                                📞 Call
                            </button>
                            <button class="btn-action btn-whatsapp" onclick="event.stopPropagation();window.open('https://wa.me/${data.phone.replace(/[^0-9]/g, '')}','_blank')">
                                💬 WhatsApp
                            </button>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

// Get priority icon
function getPriorityIcon(priority) {
    const icons = {
        'HOT': '🔥',
        'WARM': '🟡',
        'COLD': '🔵',
        'LOW': '⚪'
    };
    return icons[priority] || '⚪';
}

// Filter leads
function filterLeads() {
    const filter = document.getElementById('priorityFilter').value;
    const search = document.getElementById('searchInput').value.toLowerCase();
    
    let filtered = allLeads;
    
    if (filter !== 'all') {
        filtered = filtered.filter(l => l.score?.priority === filter);
    }
    
    if (search) {
        filtered = filtered.filter(l => {
            const data = l.data || {};
            const searchable = [
                data.name,
                data.location,
                data.property_type,
                data.phone,
                data.budget
            ].join(' ').toLowerCase();
            return searchable.includes(search);
        });
    }
    
    renderLeads(filtered);
}

// Search leads
function searchLeads() {
    filterLeads();
}

// View lead details
async function viewLead(conversationId) {
    try {
        const response = await fetch(`${API_URL}/leads/${conversationId}`);
        const lead = await response.json();
        
        const data = lead.data || {};
        const score = lead.score || {};
        const summary = lead.summary || {};
        
        const modal = document.getElementById('leadModal');
        document.getElementById('modalTitle').textContent = 
            `Lead: ${data.name || 'Unknown Customer'}`;
        
        document.getElementById('modalBody').innerHTML = `
            <div class="modal-detail">
                <span class="label">Priority</span>
                <span class="value">
                    <span class="priority-badge ${(score.priority || 'LOW').toLowerCase()}">
                        ${getPriorityIcon(score.priority)} ${score.priority || 'LOW'}
                    </span>
                </span>
            </div>
            <div class="modal-detail">
                <span class="label">Score</span>
                <span class="value"><strong>${score.score || 0}/100</strong></span>
            </div>
            <div class="modal-detail">
                <span class="label">Status</span>
                <span class="value">${score.description || 'N/A'}</span>
            </div>
            <hr style="margin:16px 0;border-color:#e2e8f0;">
            <h3 style="margin-bottom:12px;">Lead Information</h3>
            ${Object.entries(data).map(([key, value]) => `
                <div class="modal-detail">
                    <span class="label">${key.replace('_', ' ').toUpperCase()}</span>
                    <span class="value">${value || 'Not provided'}</span>
                </div>
            `).join('')}
            ${score.reasons && score.reasons.length > 0 ? `
                <hr style="margin:16px 0;border-color:#e2e8f0;">
                <h3 style="margin-bottom:12px;">✅ Qualification Signals</h3>
                ${score.reasons.map(r => `
                    <div class="modal-detail">
                        <span class="value" style="color:#16a34a;">${r}</span>
                    </div>
                `).join('')}
            ` : ''}
            ${score.missing && score.missing.length > 0 ? `
                <hr style="margin:16px 0;border-color:#e2e8f0;">
                <h3 style="margin-bottom:12px;">⚠️ Missing Information</h3>
                ${score.missing.map(m => `
                    <div class="modal-detail">
                        <span class="value" style="color:#dc2626;">• ${m}</span>
                    </div>
                `).join('')}
            ` : ''}
            ${lead.conversation ? `
                <hr style="margin:16px 0;border-color:#e2e8f0;">
                <h3 style="margin-bottom:12px;">💬 Conversation</h3>
                <div class="modal-conversation">
                    ${lead.conversation.map(msg => `
                        <div class="msg ${msg.role}">
                            <strong>${msg.role === 'user' ? 'Customer' : 'Agent'}:</strong>
                            ${msg.content}
                        </div>
                    `).join('')}
                </div>
            ` : ''}
            <hr style="margin:16px 0;border-color:#e2e8f0;">
            <div style="display:flex;gap:8px;justify-content:flex-end;">
                ${data.phone ? `
                    <button class="btn-action btn-call" onclick="window.location.href='tel:${data.phone}'">
                        📞 Call
                    </button>
                    <button class="btn-action btn-whatsapp" onclick="window.open('https://wa.me/${data.phone.replace(/[^0-9]/g, '')}','_blank')">
                        💬 WhatsApp
                    </button>
                ` : ''}
                <button class="btn-action btn-view" onclick="closeModal()">Close</button>
            </div>
        `;
        
        modal.classList.add('show');
        
    } catch (error) {
        console.error('Error loading lead details:', error);
        alert('Could not load lead details. Make sure the server is running.');
    }
}

// Close modal
function closeModal() {
    document.getElementById('leadModal').classList.remove('show');
}

// Close modal on outside click
document.getElementById('leadModal').addEventListener('click', function(e) {
    if (e.target === this) {
        closeModal();
    }
});

// Auto-refresh every 30 seconds
setInterval(loadLeads, 30000);

// Load leads on page load
document.addEventListener('DOMContentLoaded', loadLeads);