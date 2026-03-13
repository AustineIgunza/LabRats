// Global state
let currentUser = null;
let authToken = null;
let currentPage = 1;
let totalPages = 1;
let usersPerPage = 10;

// API Base URL
const API_BASE = '/api';

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    // Check if user is already logged in
    checkAuthStatus();
    
    // Set up event listeners
    setupEventListeners();
});

// Check authentication status
function checkAuthStatus() {
    const token = localStorage.getItem('authToken');
    const user = localStorage.getItem('currentUser');
    
    if (token && user) {
        authToken = token;
        currentUser = JSON.parse(user);
        showDashboard();
    } else {
        showLogin();
    }
}

// Set up event listeners
function setupEventListeners() {
    // Auth form tabs
    document.getElementById('login-tab').addEventListener('click', () => switchTab('login'));
    document.getElementById('register-tab').addEventListener('click', () => switchTab('register'));
    
    // Auth forms
    document.getElementById('login-form').addEventListener('submit', handleLogin);
    document.getElementById('register-form').addEventListener('submit', handleRegister);
    document.getElementById('profile-form').addEventListener('submit', handleProfileUpdate);
    document.getElementById('edit-user-form').addEventListener('submit', handleEditUser);
    
    // Navigation
    document.getElementById('logout-btn').addEventListener('click', handleLogout);
    
    // Pagination
    document.getElementById('prev-btn').addEventListener('click', () => changePage(currentPage - 1));
    document.getElementById('next-btn').addEventListener('click', () => changePage(currentPage + 1));
}

// Switch between login and register tabs
function switchTab(tab) {
    const loginTab = document.getElementById('login-tab');
    const registerTab = document.getElementById('register-tab');
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    
    if (tab === 'login') {
        loginTab.classList.add('active');
        registerTab.classList.remove('active');
        loginForm.classList.add('active');
        registerForm.classList.remove('active');
    } else {
        registerTab.classList.add('active');
        loginTab.classList.remove('active');
        registerForm.classList.add('active');
        loginForm.classList.remove('active');
    }
}

// Handle login
async function handleLogin(e) {
    e.preventDefault();
    
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email, password }),
        });
        
        const data = await response.json();
        
        if (response.ok) {
            authToken = data.access_token;
            currentUser = data.user;
            
            // Store in localStorage
            localStorage.setItem('authToken', authToken);
            localStorage.setItem('currentUser', JSON.stringify(currentUser));
            
            showToast('Login successful!', 'success');
            showDashboard();
        } else {
            console.error('Login failed', response.status, data);
            showToast(data.detail || JSON.stringify(data) || 'Login failed', 'error');
        }
    } catch (error) {
        console.error('Login error:', error);
        showToast('Network error occurred', 'error');
    } finally {
        showLoading(false);
    }
}

// Handle registration
async function handleRegister(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const userData = {
        email: formData.get('email'),
        username: formData.get('username'),
        full_name: formData.get('full_name'),
        password: formData.get('password'),
        role: formData.get('role'),
    };
    
    showLoading(true);
    
    try {
        const response = await fetch(`${API_BASE}/auth/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(userData),
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showToast('Registration successful! Please login.', 'success');
            switchTab('login');
            e.target.reset();
        } else {
            console.error('Registration failed', response.status, data);
            showToast(data.detail || JSON.stringify(data) || 'Registration failed', 'error');
        }
    } catch (error) {
        console.error('Registration error:', error);
        showToast('Network error occurred', 'error');
    } finally {
        showLoading(false);
    }
}

// Handle logout
async function handleLogout() {
    try {
        await fetch(`${API_BASE}/auth/logout`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
            },
        });
    } catch (error) {
        console.error('Logout error:', error);
    }
    
    // Clear local storage
    localStorage.removeItem('authToken');
    localStorage.removeItem('currentUser');
    
    authToken = null;
    currentUser = null;
    
    showToast('Logged out successfully', 'info');
    showLogin();
}

// Show login section
function showLogin() {
    document.getElementById('login-section').classList.remove('hidden');
    document.getElementById('dashboard').classList.add('hidden');
    document.getElementById('navbar').classList.add('hidden');
}

// Show dashboard
function showDashboard() {
    document.getElementById('login-section').classList.add('hidden');
    document.getElementById('dashboard').classList.remove('hidden');
    document.getElementById('navbar').classList.remove('hidden');

    // Reset sections to a clean state
    document.getElementById('user-dashboard').classList.add('hidden');
    document.getElementById('manager-dashboard').classList.add('hidden');
    document.getElementById('profile-section').classList.add('hidden');
    document.getElementById('security-logs-section').classList.add('hidden');
    document.getElementById('edit-user-modal').classList.remove('show');

    // Update navigation
    document.getElementById('user-welcome').textContent = `Welcome, ${currentUser.full_name}`;
    
    // Show appropriate dashboard sections
    if (currentUser.role === 'manager') {
        document.getElementById('manager-dashboard').classList.remove('hidden');
        loadUsers();
    } else {
        document.getElementById('user-dashboard').classList.remove('hidden');
    }
}

// Load users (manager only)
async function loadUsers(page = 1) {
    if (currentUser.role !== 'manager') return;
    
    const roleFilter = document.getElementById('role-filter')?.value || '';
    const statusFilter = document.getElementById('status-filter')?.value || '';
    
    try {
        const params = new URLSearchParams({
            page: page.toString(),
            per_page: usersPerPage.toString(),
        });
        
        if (roleFilter) params.append('role', roleFilter);
        if (statusFilter !== '') params.append('is_active', statusFilter);
        
        const response = await fetch(`${API_BASE}/admin/users?${params}`, {
            headers: {
                'Authorization': `Bearer ${authToken}`,
            },
        });
        
        const data = await response.json();
        
        if (response.ok) {
            displayUsers(data.users);
            updatePagination(data.page, Math.ceil(data.total / data.per_page), data.total);
        } else {
            showToast(data.detail || 'Failed to load users', 'error');
        }
    } catch (error) {
        console.error('Load users error:', error);
        showToast('Network error occurred', 'error');
    }
}

// Display users in table
function displayUsers(users) {
    const tbody = document.querySelector('#users-table tbody');
    
    if (users.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" class="loading">No users found</td></tr>';
        return;
    }
    
    tbody.innerHTML = users.map(user => `
        <tr>
            <td>${user.id}</td>
            <td>${user.username}</td>
            <td>${user.email}</td>
            <td>${user.full_name}</td>
            <td><span class="role-badge role-${user.role}">${user.role}</span></td>
            <td><span class="status-badge status-${user.is_active ? 'active' : 'inactive'}">${user.is_active ? 'Active' : 'Inactive'}</span></td>
            <td>${formatDate(user.created_at)}</td>
            <td>${user.last_login ? formatDate(user.last_login) : 'Never'}</td>
            <td class="actions">
                <button class="btn btn-sm btn-secondary" onclick="editUser(${user.id})">
                    <i class="fas fa-edit"></i>
                </button>
                ${user.id !== currentUser.id ? `
                <button class="btn btn-sm btn-danger" onclick="confirmDeleteUser(${user.id})">
                    <i class="fas fa-trash"></i>
                </button>
                ` : ''}
            </td>
        </tr>
    `).join('');
}

// Update pagination
function updatePagination(page, total, totalUsers) {
    currentPage = page;
    totalPages = total;
    
    const pageInfo = document.getElementById('page-info');
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    const pagination = document.getElementById('pagination');
    
    pageInfo.textContent = `Page ${page} of ${total} (${totalUsers} users)`;
    prevBtn.disabled = page <= 1;
    nextBtn.disabled = page >= total;
    
    pagination.classList.remove('hidden');
}

// Change page
function changePage(page) {
    if (page < 1 || page > totalPages) return;
    loadUsers(page);
}

// Apply filters
function applyFilters() {
    currentPage = 1;
    loadUsers(1);
}

// Refresh users list
function refreshUsersList() {
    loadUsers(currentPage);
}

// Edit user
async function editUser(userId) {
    try {
        const response = await fetch(`${API_BASE}/admin/users`, {
            headers: {
                'Authorization': `Bearer ${authToken}`,
            },
        });
        
        const data = await response.json();
        const user = data.users.find(u => u.id === userId);
        
        if (user) {
            document.getElementById('edit-user-id').value = user.id;
            document.getElementById('edit-username').value = user.username;
            document.getElementById('edit-email').value = user.email;
            document.getElementById('edit-fullname').value = user.full_name;
            document.getElementById('edit-role').value = user.role;
            document.getElementById('edit-status').value = user.is_active.toString();
            
            document.getElementById('edit-user-modal').classList.add('show');
        }
    } catch (error) {
        console.error('Edit user error:', error);
        showToast('Failed to load user data', 'error');
    }
}

// Handle edit user form
async function handleEditUser(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const userId = formData.get('id');
    const userData = {
        username: formData.get('username'),
        email: formData.get('email'),
        full_name: formData.get('full_name'),
        role: formData.get('role'),
        is_active: formData.get('is_active') === 'true',
    };
    
    try {
        const response = await fetch(`${API_BASE}/admin/users/${userId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`,
            },
            body: JSON.stringify(userData),
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showToast('User updated successfully', 'success');
            closeEditUserModal();
            loadUsers(currentPage);
        } else {
            showToast(data.detail || 'Failed to update user', 'error');
        }
    } catch (error) {
        console.error('Update user error:', error);
        showToast('Network error occurred', 'error');
    }
}

// Close edit user modal
function closeEditUserModal() {
    document.getElementById('edit-user-modal').classList.remove('show');
}

// Confirm delete user
function confirmDeleteUser(userId) {
    if (confirm('Are you sure you want to delete this user? This action cannot be undone.')) {
        deleteUser(userId);
    }
}

// Delete user
async function deleteUser(userId) {
    try {
        const response = await fetch(`${API_BASE}/admin/users/${userId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${authToken}`,
            },
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showToast('User deleted successfully', 'success');
            loadUsers(currentPage);
        } else {
            showToast(data.detail || 'Failed to delete user', 'error');
        }
    } catch (error) {
        console.error('Delete user error:', error);
        showToast('Network error occurred', 'error');
    }
}

// Show user profile
function showUserProfile() {
    document.getElementById('user-dashboard').classList.add('hidden');
    document.getElementById('manager-dashboard').classList.add('hidden');
    document.getElementById('profile-section').classList.remove('hidden');
    
    // Populate profile form
    document.getElementById('profile-username').value = currentUser.username;
    document.getElementById('profile-email').value = currentUser.email;
    document.getElementById('profile-fullname').value = currentUser.full_name;
}

// Hide user profile
function hideUserProfile() {
    document.getElementById('profile-section').classList.add('hidden');
    if (currentUser.role === 'manager') {
        document.getElementById('manager-dashboard').classList.remove('hidden');
    } else {
        document.getElementById('user-dashboard').classList.remove('hidden');
    }
}

// Handle profile update
async function handleProfileUpdate(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const userData = {
        username: formData.get('username'),
        email: formData.get('email'),
        full_name: formData.get('full_name'),
    };
    
    try {
        const response = await fetch(`${API_BASE}/users/me`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`,
            },
            body: JSON.stringify(userData),
        });
        
        const data = await response.json();
        
        if (response.ok) {
            currentUser = data;
            localStorage.setItem('currentUser', JSON.stringify(currentUser));
            document.getElementById('user-welcome').textContent = `Welcome, ${currentUser.full_name}`;
            
            showToast('Profile updated successfully', 'success');
        } else {
            showToast(data.detail || 'Failed to update profile', 'error');
        }
    } catch (error) {
        console.error('Profile update error:', error);
        showToast('Network error occurred', 'error');
    }
}

// Show security logs
function showSecurityLogs() {
    document.getElementById('manager-dashboard').classList.add('hidden');
    document.getElementById('security-logs-section').classList.remove('hidden');
    loadSecurityLogs();
}

// Hide security logs
function hideSecurityLogs() {
    document.getElementById('security-logs-section').classList.add('hidden');
    document.getElementById('manager-dashboard').classList.remove('hidden');
}

// Load security logs
async function loadSecurityLogs() {
    if (currentUser.role !== 'manager') return;
    
    const emailFilter = document.getElementById('log-email-filter')?.value || '';
    const successFilter = document.getElementById('log-success-filter')?.value || '';
    const hoursFilter = document.getElementById('log-hours-filter')?.value || '24';
    
    try {
        const params = new URLSearchParams({
            hours: hoursFilter,
        });
        
        if (emailFilter) params.append('email', emailFilter);
        if (successFilter !== '') params.append('success', successFilter);
        
        const response = await fetch(`${API_BASE}/admin/login-attempts?${params}`, {
            headers: {
                'Authorization': `Bearer ${authToken}`,
            },
        });
        
        const data = await response.json();
        
        if (response.ok) {
            displaySecurityLogs(data);
        } else {
            showToast(data.detail || 'Failed to load security logs', 'error');
        }
    } catch (error) {
        console.error('Load security logs error:', error);
        showToast('Network error occurred', 'error');
    }
}

// Display security logs
function displaySecurityLogs(logs) {
    const tbody = document.querySelector('#logs-table tbody');
    
    if (logs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="loading">No logs found</td></tr>';
        return;
    }
    
    tbody.innerHTML = logs.map(log => `
        <tr>
            <td>${formatDateTime(log.attempted_at)}</td>
            <td>${log.email}</td>
            <td>${log.ip_address}</td>
            <td><span class="status-badge status-${log.success ? 'success' : 'failed'}">${log.success ? 'Success' : 'Failed'}</span></td>
            <td title="${log.user_agent}">${truncateText(log.user_agent || 'Unknown', 50)}</td>
        </tr>
    `).join('');
}

// Refresh security logs
function refreshSecurityLogs() {
    loadSecurityLogs();
}

// Utility functions
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString();
}

function formatDateTime(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleString();
}

function truncateText(text, maxLength) {
    if (!text) return '';
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
}

// Show loading overlay
function showLoading(show) {
    const overlay = document.getElementById('loading-overlay');
    if (show) {
        overlay.classList.remove('hidden');
    } else {
        overlay.classList.add('hidden');
    }
}

// Show toast notification
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icons = {
        success: 'fas fa-check-circle',
        error: 'fas fa-exclamation-circle',
        warning: 'fas fa-exclamation-triangle',
        info: 'fas fa-info-circle'
    };
    
    toast.innerHTML = `
        <i class="toast-icon ${icons[type]}"></i>
        <span class="toast-message">${message}</span>
        <button class="toast-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    container.appendChild(toast);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (toast.parentElement) {
            toast.remove();
        }
    }, 5000);
}

// Handle API errors globally
window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
    showToast('An unexpected error occurred', 'error');
});

// Handle network errors
window.addEventListener('online', function() {
    showToast('Connection restored', 'success');
});

window.addEventListener('offline', function() {
    showToast('Connection lost. Some features may not work.', 'warning');
});
