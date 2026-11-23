/**
 * TimetablePro - Global Application Shell & Utility Engine
 * Initializes Lucide icons, toast notifications, notification drawer,
 * modal dialogs, and mobile sidebar navigation.
 */

// Initialize Lucide icons on document ready
document.addEventListener('DOMContentLoaded', () => {
    initLucideIcons();
    pollNotifications();
});

function initLucideIcons() {
    if (window.lucide) {
        window.lucide.createIcons();
    }
}

/**
 * Standardized API fetch wrapper with JSON parsing and error handling
 */
async function apiCall(endpoint, method = 'GET', data = null) {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    };
    if (data && (method === 'POST' || method === 'PUT' || method === 'DELETE')) {
        options.body = JSON.stringify(data);
    }
    try {
        const response = await fetch(endpoint, options);
        if (response.status === 401) {
            window.location.href = '/login';
            return { success: False, message: "Session expired. Redirecting to login." };
        }
        const result = await response.json();
        return result;
    } catch (err) {
        console.error(`API Call failed on ${endpoint}:`, err);
        return { success: false, message: "Network or server connection failed." };
    }
}

/**
 * Modern SaaS Toast Notification
 */
function showToast(message, type = 'primary') {
    let stack = document.getElementById('toastStack');
    if (!stack) {
        stack = document.createElement('div');
        stack.id = 'toastStack';
        stack.className = 'toast-stack';
        document.body.appendChild(stack);
    }

    const toast = document.createElement('div');
    toast.className = `toast-msg ${type}`;
    
    // Choose Lucide icon name according to type
    let iconName = 'info';
    if (type === 'success') iconName = 'check-circle';
    if (type === 'danger') iconName = 'alert-triangle';
    if (type === 'warning') iconName = 'alert-circle';

    toast.innerHTML = `
        <i data-lucide="${iconName}" style="width: 18px; height: 18px; flex-shrink: 0;"></i>
        <div style="flex: 1; font-weight: 500;">${message}</div>
    `;

    stack.appendChild(toast);
    initLucideIcons();

    setTimeout(() => {
        toast.style.transition = 'all 0.3s ease';
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => toast.remove(), 300);
    }, 3800);
}

/**
 * Sidebar Toggle for Tablets & Mobile
 */
function toggleSidebar() {
    const sidebar = document.getElementById('appSidebar');
    if (sidebar) {
        sidebar.classList.toggle('open');
    }
}

/**
 * Notification Panel & Feed
 */
function toggleNotifications() {
    const drawer = document.getElementById('notifDrawer');
    if (drawer) {
        drawer.classList.toggle('open');
        if (drawer.classList.contains('open')) {
            loadNotifications();
        }
    }
}

async function pollNotifications() {
    const res = await apiCall('/api/notifications');
    if (res.success) {
        const badge = document.getElementById('notifCountBadge');
        if (badge) {
            if (res.unread_count > 0) {
                badge.textContent = res.unread_count;
                badge.style.display = 'flex';
            } else {
                badge.style.display = 'none';
            }
        }
    }
}

async function loadNotifications() {
    const body = document.getElementById('notifDrawerBody');
    if (!body) return;

    body.innerHTML = '<div style="padding: 2rem; text-align: center; color: var(--slate-400);">Loading notifications...</div>';

    const res = await apiCall('/api/notifications');
    if (!res.success || !res.notifications || res.notifications.length === 0) {
        body.innerHTML = `
            <div style="padding: 2.5rem 1rem; text-align: center; color: var(--slate-400);">
                <i data-lucide="bell-off" style="width: 32px; height: 32px; stroke-width: 1.5; margin-bottom: 0.5rem;"></i>
                <div>No notifications available.</div>
            </div>
        `;
        initLucideIcons();
        return;
    }

    body.innerHTML = res.notifications.map(n => `
        <div class="notif-card-item ${n.is_read ? '' : 'unread'}" onclick="markNotificationRead('${n.id}', '${n.link || ''}')">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.25rem;">
                <strong style="font-size: 0.825rem; color: var(--slate-900);">${n.title}</strong>
                <span style="font-size: 0.68rem; color: var(--slate-400);">${formatDate(n.created_at)}</span>
            </div>
            <div style="font-size: 0.775rem; color: var(--slate-600);">${n.message}</div>
        </div>
    `).join('');

    initLucideIcons();
}

async function markNotificationRead(id, link) {
    await apiCall(`/api/notifications/${id}/read`, 'POST');
    pollNotifications();
    loadNotifications();
    if (link && link !== 'null' && link !== '') {
        window.location.href = link;
    }
}

async function markAllNotificationsRead() {
    await apiCall('/api/notifications/mark-all-read', 'POST');
    pollNotifications();
    loadNotifications();
    showToast('All notifications marked as read.', 'info');
}

/**
 * Format ISO datetime string into readable text
 */
function formatDate(isoStr) {
    if (!isoStr) return '';
    try {
        const d = new Date(isoStr);
        return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
    } catch {
        return isoStr;
    }
}

/**
 * Bento section switcher
 */
function showBentoSection(sectionId) {
    document.querySelectorAll('.bento-section').forEach(sec => {
        sec.style.display = 'none';
    });
    document.querySelectorAll('.nav-link-item').forEach(item => {
        item.classList.remove('active');
        if (item.dataset.section === sectionId) {
            item.classList.add('active');
        }
    });

    const target = document.getElementById(`section-${sectionId}`);
    if (target) {
        target.style.display = 'block';
    }

    // Close mobile sidebar upon selection
    const sidebar = document.getElementById('appSidebar');
    if (sidebar) sidebar.classList.remove('open');

    // Re-trigger Lucide icons for freshly displayed elements
    initLucideIcons();
}
