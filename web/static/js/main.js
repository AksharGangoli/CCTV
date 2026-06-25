/**
 * CCTV Smart Monitor - Dashboard JavaScript
 * Handles real-time updates and interactions
 */

// Update clock
function updateClock() {
    const now = new Date();
    const options = { 
        hour: '2-digit', minute: '2-digit', second: '2-digit',
        hour12: true, day: '2-digit', month: 'short', year: 'numeric'
    };
    const timeEl = document.getElementById('current-time');
    if (timeEl) {
        timeEl.textContent = now.toLocaleString('en-IN', options);
    }
}
setInterval(updateClock, 1000);
updateClock();

// Auto-refresh dashboard stats
function refreshStats() {
    fetch('/api/summary')
        .then(r => r.json())
        .then(data => {
            // Update stats cards if they exist
            const elements = {
                'entries-count': data.entries,
                'exits-count': data.exits,
                'inside-count': data.current_inside
            };
            
            for (const [id, value] of Object.entries(elements)) {
                const el = document.getElementById(id);
                if (el) el.textContent = value || 0;
            }
        })
        .catch(err => console.log('Stats refresh error:', err));
}

// Refresh every 5 seconds
setInterval(refreshStats, 5000);

// Notification sound
function playNotificationSound() {
    try {
        const audio = new Audio('data:audio/wav;base64,UklGRl9vT19XQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQ==');
        audio.play().catch(() => {});
    } catch(e) {}
}

// Helper: Show toast notification
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed; bottom: 20px; right: 20px;
        padding: 15px 25px; border-radius: 8px;
        color: white; font-size: 0.9rem; z-index: 9999;
        animation: slideIn 0.3s ease;
    `;
    
    const colors = { info: '#2563eb', success: '#10b981', error: '#ef4444', warning: '#f59e0b' };
    toast.style.background = colors[type] || colors.info;
    
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
}

console.log('CCTV Smart Monitor Dashboard loaded');
