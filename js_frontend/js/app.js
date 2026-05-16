/**
 * Yoga Assessment System - Main Application
 */

// Initialize API client - 使用 Python Flask 后端
const api = new YogaAPI('http://localhost:5000/api');

// App State
let appState = {
    selectedVideo: null,
    selectedPose: 'Mountain Pose',  // 默认值，必须与后端数据匹配
    poseStandards: [],
    currentAssessmentId: null,
    assessmentResult: null,
    auth: {
        loggedIn: false,
        user: null
    }
};

// 中英文映射 - 必须与后端数据匹配
const poseNameMap = {
    '山式': 'Mountain Pose',
    '树式': 'Tree Pose',
    '战士二式': 'Warrior II',
    '三角式': 'Triangle Pose',
    '椅子式': 'Chair Pose',
    '半月式': 'Half Moon Pose'
};

// DOM Elements
const elements = {
    uploadArea: document.getElementById('upload-area'),
    videoInput: document.getElementById('video-input'),
    uploadPreview: document.getElementById('upload-preview'),
    previewVideo: document.getElementById('preview-video'),
    poseGrid: document.getElementById('pose-grid'),
    assessBtn: document.getElementById('assess-btn'),
    resultSection: document.getElementById('result-section'),
    processingOverlay: document.getElementById('processing-overlay'),
    historyList: document.getElementById('history-list'),
    navProfile: document.getElementById('nav-profile'),
    navAdmin: document.getElementById('nav-admin'),
    navLogin: document.getElementById('nav-login'),
    navRegister: document.getElementById('nav-register'),
    navLogout: document.getElementById('nav-logout'),
    loginForm: document.getElementById('login-form'),
    registerForm: document.getElementById('register-form'),
    adminCreateForm: document.getElementById('admin-create-user-form'),
    refreshUsersBtn: document.getElementById('refresh-users-btn'),
    adminCreateError: document.getElementById('admin-create-error'),
    adminCreateSuccess: document.getElementById('admin-create-success'),
    adminUserTable: document.getElementById('admin-user-table'),
    loginError: document.getElementById('login-error'),
    registerError: document.getElementById('register-error'),
    profileUsername: document.getElementById('profile-username'),
    profileEmail: document.getElementById('profile-email'),
    profileRole: document.getElementById('profile-role'),
    profileStatus: document.getElementById('profile-status')
};

/**
 * Initialize Application
 */
async function initApp() {
    try {
        await loadAuthState();
        await loadPoseStandards();
        await loadStats();
        setupEventListeners();
        console.log('Application initialized');
    } catch (error) {
        console.error('Initialization error:', error);
        showOfflineMode();
    }
}

/**
 * Load pose standards
 */
async function loadPoseStandards() {
    try {
        appState.poseStandards = await api.getPoseStandards();
        renderPoseGrid();
    } catch (error) {
        console.warn('Using default pose standards');
        appState.poseStandards = [
            { pose_name: '下犬式', pose_name_en: 'Downward Dog', difficulty_level: '初级' },
            { pose_name: '树式', pose_name_en: 'Tree Pose', difficulty_level: '初级' },
            { pose_name: '战士一式', pose_name_en: 'Warrior I', difficulty_level: '中级' },
            { pose_name: '三角式', pose_name_en: 'Triangle Pose', difficulty_level: '中级' },
            { pose_name: '半月式', pose_name_en: 'Half Moon Pose', difficulty_level: '中级' }
        ];
        renderPoseGrid();
    }
}

/**
 * Load system statistics
 */
async function loadStats() {
    try {
        const stats = await api.getStats();
        document.getElementById('total-assessments').textContent = stats.total_assessments || 0;
        document.getElementById('total-users').textContent = stats.total_users || 0;
        // 使用 avg_score 而不是 average_score
        document.getElementById('avg-score').textContent = (stats.avg_score || 0).toFixed(1);
    } catch (error) {
        console.warn('Could not load stats:', error);
        // 设置默认值
        document.getElementById('total-assessments').textContent = '0';
        document.getElementById('total-users').textContent = '0';
        document.getElementById('avg-score').textContent = '0.0';
    }
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Navigation
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const page = e.target.closest('.nav-link').dataset.page;
            if (page) {
                switchPage(page);
            }
        });
    });

    // Logout button
    elements.navLogout.addEventListener('click', async (e) => {
        e.preventDefault();
        await performLogout();
    });

    if (elements.refreshUsersBtn) {
        elements.refreshUsersBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            await loadAdminUsers();
        });
    }

    if (elements.adminCreateForm) {
        elements.adminCreateForm.addEventListener('submit', handleCreateAdminUserSubmit);
    }

    // File upload
    elements.uploadArea.addEventListener('click', () => elements.videoInput.click());
    elements.videoInput.addEventListener('change', handleVideoSelect);

    // Drag and drop
    elements.uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        elements.uploadArea.style.borderColor = 'var(--primary)';
    });
    elements.uploadArea.addEventListener('dragleave', () => {
        elements.uploadArea.style.borderColor = '';
    });
    elements.uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        elements.uploadArea.style.borderColor = '';
        const files = e.dataTransfer.files;
        if (files.length > 0 && files[0].type.startsWith('video/')) {
            handleVideoFile(files[0]);
        }
    });

    // Assess button
    elements.assessBtn.addEventListener('click', startAssessment);

    // Auth forms
    if (elements.loginForm) {
        elements.loginForm.addEventListener('submit', handleLoginSubmit);
    }
    if (elements.registerForm) {
        elements.registerForm.addEventListener('submit', handleRegisterSubmit);
    }
    if (elements.adminCreateForm) {
        elements.adminCreateForm.addEventListener('submit', handleCreateAdminUserSubmit);
    }
    if (elements.refreshUsersBtn) {
        elements.refreshUsersBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            await loadAdminUsers();
        });
    }

    document.getElementById('show-register')?.addEventListener('click', (e) => {
        e.preventDefault();
        switchPage('register');
    });
    document.getElementById('show-login')?.addEventListener('click', (e) => {
        e.preventDefault();
        switchPage('login');
    });
}

/**
 * Switch page
 */
function switchPage(pageName) {
    const authRequiredPages = ['assessment', 'history', 'profile', 'admin'];

    if (authRequiredPages.includes(pageName) && !appState.auth.loggedIn) {
        pageName = 'login';
    }

    if (pageName === 'admin' && appState.auth.loggedIn && appState.auth.user?.role !== 'admin') {
        pageName = 'home';
    }

    if (!pageName || !document.getElementById(`page-${pageName}`)) {
        pageName = appState.auth.loggedIn ? 'home' : 'login';
    }

    // Update navigation
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.toggle('active', link.dataset.page === pageName);
    });

    // Update pages
    document.querySelectorAll('.page').forEach(page => {
        page.classList.toggle('active', page.id === `page-${pageName}`);
    });

    if (pageName === 'history') {
        loadHistory();
    }

    if (pageName === 'profile') {
        renderProfile();
    }

    if (pageName === 'admin') {
        loadAdminUsers();
    }
}


/**
 * Handle video selection
 */
function handleVideoSelect(e) {
    const file = e.target.files[0];
    if (file) {
        handleVideoFile(file);
    }
}

/**
 * Handle video file
 */
function handleVideoFile(file) {
    // Validate file
    if (file.size > 100 * 1024 * 1024) {
        alert('文件大小不能超过100MB');
        return;
    }

    const validTypes = ['video/mp4', 'video/avi', 'video/quicktime'];
    if (!validTypes.includes(file.type)) {
        alert('不支持的视频格式');
        return;
    }

    appState.selectedVideo = file;

    // Show preview
    const url = URL.createObjectURL(file);
    elements.previewVideo.src = url;
    elements.uploadArea.style.display = 'none';
    elements.uploadPreview.style.display = 'block';

    // Enable assess button
    elements.assessBtn.disabled = false;
}

/**
 * Clear selected video
 */
function clearVideo() {
    appState.selectedVideo = null;
    elements.previewVideo.src = '';
    elements.uploadArea.style.display = 'block';
    elements.uploadPreview.style.display = 'none';
    elements.assessBtn.disabled = true;
}

/**
 * Render pose selection grid
 */
function renderPoseGrid() {
    const icons = {
        'Mountain Pose': 'fa-mountain',
        'Tree Pose': 'fa-tree',
        'Warrior II': 'fa-shield-alt',
        'Triangle Pose': 'fa-triangle',
        'Chair Pose': 'fa-chair',
        'Half Moon Pose': 'fa-moon'
    };
    
    // 反向映射：英文 -> 中文
    const EnglishToChinese = Object.entries(poseNameMap).reduce((acc, [cn, en]) => {
        acc[en] = cn;
        return acc;
    }, {});

    elements.poseGrid.innerHTML = appState.poseStandards.map(pose => {
        const englishName = pose.pose_name;
        const chineseName = EnglishToChinese[englishName] || englishName;
        const isSelected = englishName === appState.selectedPose;
        
        return `
            <div class="pose-card ${isSelected ? 'selected' : ''}"
                 data-pose="${englishName}">
                <i class="fas ${icons[englishName] || icons[chineseName] || 'fa-user'}"></i>
                <h4>${chineseName}</h4>
                <span>${pose.difficulty_level || ''}</span>
            </div>
        `;
    }).join('');

    // Add click handlers
    document.querySelectorAll('.pose-card').forEach(card => {
        card.addEventListener('click', () => {
            document.querySelectorAll('.pose-card').forEach(c => c.classList.remove('selected'));
            card.classList.add('selected');
            appState.selectedPose = card.dataset.pose;  // 使用英文名
        });
    });
}

/**
 * Start assessment
 */
async function startAssessment() {
    if (!appState.selectedVideo) {
        alert('请先选择视频');
        return;
    }

    // Show processing overlay
    elements.processingOverlay.style.display = 'flex';
    const progressFill = document.getElementById('progress-fill');
    progressFill.style.width = '10%';

    try {
        // 先上传视频拿到任务 id，后续评估进度由轮询接口驱动。
        const uploadResult = await api.uploadVideo(
            appState.selectedVideo,
            appState.selectedPose
        );

        // 后端返回 id，不是 assessment_id
        appState.currentAssessmentId = uploadResult.id || uploadResult.assessment_id;
        progressFill.style.width = '50%';

        // 轮询期间只更新进度条，不直接假设后端已经生成结果。
        const result = await api.pollAssessment(
            appState.currentAssessmentId,
            (status) => {
                if (status.progress) {
                    progressFill.style.width = `${status.progress}%`;
                }
            }
        );

        appState.assessmentResult = result;
        progressFill.style.width = '100%';

        // 等进度动画收尾后再切换结果区，避免界面突然跳变。
        setTimeout(() => {
            elements.processingOverlay.style.display = 'none';
            showResults(result);
        }, 500);

    } catch (error) {
        console.error('Assessment error:', error);
        alert('评估失败: ' + error.message);
        elements.processingOverlay.style.display = 'none';
    }
}

/**
 * Show assessment results
 */
function showResults(result) {
    elements.resultSection.style.display = 'block';
    // 后端可能因模型兜底返回空数组，这里统一做类型保护，避免渲染报错。
    const angleData = result.angle_data || {};
    const problems = Array.isArray(result.problems) ? result.problems : [];
    const suggestions = Array.isArray(result.suggestions) ? result.suggestions : [];

    // Animate total score
    animateScore('total-score', result.total_score);
    animateScoreRing(result.total_score);

    // Structure score
    document.getElementById('structure-score').textContent = `${result.structure_score.toFixed(0)}/60`;
    document.getElementById('structure-fill').style.width = `${(result.structure_score / 60) * 100}%`;

    // Alignment score
    document.getElementById('alignment-score').textContent = `${result.alignment_score.toFixed(0)}/30`;
    document.getElementById('alignment-fill').style.width = `${(result.alignment_score / 30) * 100}%`;

    // Stability score
    document.getElementById('stability-score').textContent = `${result.stability_score.toFixed(0)}/10`;
    document.getElementById('stability-fill').style.width = `${(result.stability_score / 10) * 100}%`;

    // Render angle chart
    renderAngleChart(angleData);

    // Render problems
    const problemsList = document.getElementById('problems-list');
    problemsList.innerHTML = problems.map(p => `<li>${p}</li>`).join('');

    // Render suggestions
    const suggestionsList = document.getElementById('suggestions-list');
    suggestionsList.innerHTML = suggestions.map(s => `<li>${s}</li>`).join('');

    // Scroll to results
    elements.resultSection.scrollIntoView({ behavior: 'smooth' });
}

/**
 * Animate score number
 */
function animateScore(elementId, targetScore) {
    const element = document.getElementById(elementId);
    let current = 0;
    const increment = targetScore / 30;
    const interval = setInterval(() => {
        current += increment;
        if (current >= targetScore) {
            current = targetScore;
            clearInterval(interval);
        }
        element.textContent = current.toFixed(0);
    }, 30);
}

/**
 * Animate score ring
 */
function animateScoreRing(score) {
    const ring = document.getElementById('score-ring');
    const circumference = 2 * Math.PI * 50; // radius = 50
    const offset = circumference - (score / 100) * circumference;
    ring.style.strokeDashoffset = offset;
}

/**
 * Render angle chart
 */
function renderAngleChart(angleData) {
    const canvas = document.getElementById('angle-chart');
    const ctx = canvas.getContext('2d');

    // Set canvas size
    canvas.width = canvas.parentElement.clientWidth;
    canvas.height = 250;

    // 后端实际返回的是统计对象：{ mean: {...}, std: {...} }。
    // 这里优先显示平均角度，同时兼容旧版直接扁平返回角度的格式。
    const meanAngles = angleData && typeof angleData.mean === 'object'
        ? angleData.mean
        : angleData || {};

    const labels = ['左肘', '右肘', '左膝', '右膝', '左髋', '右髋', '左肩', '右肩'];
    const values = [
        meanAngles.left_elbow || 0,
        meanAngles.right_elbow || 0,
        meanAngles.left_knee || 0,
        meanAngles.right_knee || 0,
        meanAngles.left_hip || 0,
        meanAngles.right_hip || 0,
        meanAngles.left_shoulder || 0,
        meanAngles.right_shoulder || 0
    ];

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw chart
    const padding = 40;
    const chartWidth = canvas.width - padding * 2;
    const chartHeight = canvas.height - padding * 2;
    const barWidth = chartWidth / labels.length - 10;

    // Draw bars
    values.forEach((value, index) => {
        const x = padding + index * (barWidth + 10) + 5;
        const barHeight = (value / 180) * chartHeight;
        const y = canvas.height - padding - barHeight;

        // Bar gradient
        const gradient = ctx.createLinearGradient(x, y, x, y + barHeight);
        gradient.addColorStop(0, '#6366f1');
        gradient.addColorStop(1, '#10b981');

        ctx.fillStyle = gradient;
        ctx.fillRect(x, y, barWidth, barHeight);

        // Value label
        ctx.fillStyle = '#374151';
        ctx.font = '12px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(`${value.toFixed(0)}°`, x + barWidth / 2, y - 5);

        // Label
        ctx.fillStyle = '#6b7280';
        ctx.fillText(labels[index], x + barWidth / 2, canvas.height - padding + 20);
    });

    // Draw baseline
    ctx.strokeStyle = '#e5e7eb';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(padding, canvas.height - padding);
    ctx.lineTo(canvas.width - padding, canvas.height - padding);
    ctx.stroke();
}

/**
 * Load assessment history
 */
async function loadHistory() {
    try {
        const data = await api.getUserAssessments();
        // 兼容新旧接口：有的版本直接返回数组，有的版本包在 assessments 字段中。
        const assessments = Array.isArray(data) ? data : (data.assessments || []);

        if (!assessments.length) {
            elements.historyList.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-history"></i>
                    <p>暂无评估历史</p>
                </div>
            `;
            return;
        }

        elements.historyList.innerHTML = assessments.map(item => {
            // 历史记录来自数据库归档，字段可能随版本演进，因此渲染时保留兜底值。
            const timestamp = new Date(item.created_at || item.timestamp || Date.now()).toLocaleString();
            const statusText = item.status ? item.status.toUpperCase() : 'COMPLETED';
            const score = item.total_score?.toFixed ? item.total_score.toFixed(0) : item.total_score || 'N/A';
            const summary = item.summary || item.result_summary || item.notes || '';

            return `
                <div class="history-card">
                    <div class="history-header">
                        <div>
                            <h4>${item.pose_name || '未知动作'}</h4>
                            <span class="history-meta">${timestamp}</span>
                        </div>
                        <span class="badge ${statusText === 'COMPLETED' ? 'badge-success' : 'badge-warning'}">${statusText}</span>
                    </div>
                    <div class="history-body">
                        <div class="history-row">
                            <span>得分</span>
                            <strong>${score}</strong>
                        </div>
                        <div class="history-row">
                            <span>等级</span>
                            <strong>${item.pose_level || item.difficulty_level || '未知'}</strong>
                        </div>
                        ${summary ? `<p class="history-summary">${summary}</p>` : ''}
                    </div>
                </div>
            `;
        }).join('');
    } catch (error) {
        console.error('加载历史失败', error);
        elements.historyList.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-exclamation-triangle"></i>
                <p>无法加载历史记录，请检查网络或重新登录。</p>
            </div>
        `;
    }
}

async function loadAuthState() {
    if (api.isAuthenticated()) {
        try {
            const user = await api.getProfile();
            setAuthState(user);
            return;
        } catch (error) {
            console.warn('Profile fetch failed, trying token refresh', error);
            const refreshed = await api.refreshTokenIfNeeded();
            if (refreshed) {
                try {
                    const user = await api.getProfile();
                    setAuthState(user);
                    return;
                } catch (innerError) {
                    console.error('Profile fetch after refresh failed', innerError);
                }
            }
        }
    }

    clearAuthState();
}

function setAuthState(user) {
    appState.auth.loggedIn = true;
    appState.auth.user = user;
    api.user = user;
    updateAuthUI();
}

function clearAuthState() {
    appState.auth.loggedIn = false;
    appState.auth.user = null;
    api.clearSession();
    updateAuthUI();
}

function updateAuthUI() {
    const loggedIn = appState.auth.loggedIn;
    const isAdmin = loggedIn && appState.auth.user?.role === 'admin';

    elements.navProfile.style.display = loggedIn ? 'inline-flex' : 'none';
    elements.navAdmin.style.display = isAdmin ? 'inline-flex' : 'none';
    elements.navLogout.style.display = loggedIn ? 'inline-flex' : 'none';
    elements.navLogin.style.display = loggedIn ? 'none' : 'inline-flex';
    elements.navRegister.style.display = loggedIn ? 'none' : 'inline-flex';

    const banner = document.getElementById('user-banner');
    const welcomeName = document.getElementById('user-welcome-name');
    const roleLabel = document.getElementById('user-role-label');

    if (loggedIn && appState.auth.user) {
        elements.profileUsername.textContent = appState.auth.user.username || '-';
        elements.profileEmail.textContent = appState.auth.user.email || '-';
        elements.profileRole.textContent = capitalizeRole(appState.auth.user.role);
        elements.profileStatus.textContent = appState.auth.user.is_active !== false ? 'Active' : 'Disabled';

        banner.style.display = 'flex';
        welcomeName.textContent = `欢迎，${appState.auth.user.username || '用户'}！`;
        roleLabel.textContent = `当前角色：${capitalizeRole(appState.auth.user.role)}`;
        roleLabel.className = `role-label role-${appState.auth.user.role || 'learner'}`;
        document.getElementById('role-info').textContent = getRoleDescription(appState.auth.user.role);
    } else {
        banner.style.display = 'none';
        welcomeName.textContent = '';
        roleLabel.textContent = '';
        document.getElementById('role-info').textContent = '登录后可查看您的评估历史、上传视频并获取个性化瑜伽动作建议。';
    }
}

function capitalizeRole(role) {
    if (!role) return 'Learner';
    return role.charAt(0).toUpperCase() + role.slice(1);
}

function getRoleDescription(role) {
    switch (role) {
        case 'admin':
            return '管理员拥有全部用户管理权限，可查看系统概况、管理用户以及审核教练申请。';
        default:
            return '学习者可以上传视频、查看评估历史，并获得个性化动作优化建议。';
    }
}

async function handleLoginSubmit(event) {
    event.preventDefault();
    elements.loginError.textContent = '';

    const username = document.getElementById('login-username').value.trim();
    const password = document.getElementById('login-password').value;

    try {
        const user = await api.login(username, password);
        setAuthState(user);
        switchPage('assessment');
    } catch (error) {
        console.error('登录失败', error);
        elements.loginError.textContent = error.message || '登录失败，请重试';
    }
}

async function handleRegisterSubmit(event) {
    event.preventDefault();
    elements.registerError.textContent = '';

    const username = document.getElementById('register-username').value.trim();
    const email = document.getElementById('register-email').value.trim();
    const password = document.getElementById('register-password').value;

    try {
        const user = await api.register(username, password, email);
        setAuthState(user);
        switchPage('assessment');
    } catch (error) {
        console.error('注册失败', error);
        elements.registerError.textContent = error.message || '注册失败，请重试';
    }
}

async function handleCreateAdminUserSubmit(event) {
    event.preventDefault();
    elements.adminCreateError.textContent = '';
    elements.adminCreateSuccess.textContent = '';

    const username = document.getElementById('admin-username').value.trim();
    const email = document.getElementById('admin-email').value.trim();
    const password = document.getElementById('admin-password').value;
    const role = document.getElementById('admin-role').value;

    try {
        const user = await api.createUser(username, password, email, role);
        elements.adminCreateSuccess.textContent = `用户 ${user.username} 创建成功`;
        elements.adminCreateForm.reset();
        await loadAdminUsers();
    } catch (error) {
        console.error('创建用户失败', error);
        elements.adminCreateError.textContent = error.message || '创建用户失败，请重试';
    }
}

async function loadAdminUsers() {
    if (!appState.auth.loggedIn || appState.auth.user?.role !== 'admin') {
        return;
    }

    try {
        const users = await api.getUsers();
        renderAdminUsers(Array.isArray(users) ? users : (users.data || users.users || []));
    } catch (error) {
        console.error('管理员用户列表加载失败', error);
        const tbody = elements.adminUserTable.querySelector('tbody');
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="empty-state">
                    无法加载用户列表，请刷新或重新登录。
                </td>
            </tr>
        `;
    }
}

function renderAdminUsers(users) {
    const tbody = elements.adminUserTable.querySelector('tbody');
    if (!Array.isArray(users) || !users.length) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="empty-state">
                    暂无用户数据。
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = users.map(user => {
const activeLabel = user.is_active ? '禁用' : '启用';
        const roleOptions = ['learner', 'admin'].map(role => `
            <option value="${role}" ${user.role === role ? 'selected' : ''}>
                ${capitalizeRole(role)}
            </option>
        `).join('');

        return `
            <tr data-user-id="${user.id}">
                <td>${user.username}</td>
                <td>${user.email || '—'}</td>
                <td>
                    <select class="admin-role-select" data-user-id="${user.id}">
                        ${roleOptions}
                    </select>
                </td>
                <td>
                    <button class="btn btn-secondary btn-sm admin-toggle-active" data-user-id="${user.id}" data-active="${user.is_active ? '1' : '0'}">
                        ${activeLabel}
                    </button>
                </td>
                <td>
                    <button class="btn btn-primary btn-sm admin-user-save" data-user-id="${user.id}">
                        保存
                    </button>
                </td>
            </tr>
        `;
    }).join('');

    tbody.querySelectorAll('.admin-user-save').forEach(button => {
        button.addEventListener('click', async (e) => {
            const userId = Number(e.currentTarget.dataset.userId);
            const row = document.querySelector(`tr[data-user-id="${userId}"]`);
            const role = row.querySelector('.admin-role-select').value;
            const activeButton = row.querySelector('.admin-toggle-active');
            const isActive = activeButton.dataset.active === '1';
            await updateAdminUser(userId, role, isActive);
        });
    });

    tbody.querySelectorAll('.admin-toggle-active').forEach(button => {
        button.addEventListener('click', (e) => {
            e.preventDefault();
            const current = e.currentTarget.dataset.active === '1';
            const nextActive = !current;
            e.currentTarget.dataset.active = nextActive ? '1' : '0';
            e.currentTarget.textContent = nextActive ? '禁用' : '启用';
        });
    });
}

async function updateAdminUser(userId, role, isActive) {
    try {
        await api.updateUser(userId, role, isActive);
        await loadAdminUsers();
    } catch (error) {
        console.error('更新用户失败', error);
        alert(error.message || '更新用户失败');
    }
}

async function performLogout() {
    try {
        await api.logout();
    } catch (error) {
        console.warn('Logout request failed, clearing session anyway', error);
    }
    clearAuthState();
    switchPage('home');
}

function renderProfile() {
    if (!appState.auth.loggedIn) {
        switchPage('login');
        return;
    }

    if (appState.auth.user) {
        elements.profileUsername.textContent = appState.auth.user.username || '-';
        elements.profileEmail.textContent = appState.auth.user.email || '-';
        elements.profileRole.textContent = capitalizeRole(appState.auth.user.role);
        elements.profileStatus.textContent = appState.auth.user.is_active !== false ? 'Active' : 'Disabled';
        document.getElementById('role-info').textContent = getRoleDescription(appState.auth.user.role);
    }
}

/**
 * Show offline mode message
 */
function showOfflineMode() {
    const header = document.querySelector('.header');
    const offlineNotice = document.createElement('div');
    offlineNotice.className = 'offline-notice';
    offlineNotice.innerHTML = `
        <i class="fas fa-wifi"></i>
        当前处于离线模式，请确保后端服务已启动 (http://localhost:8080)
    `;
    offlineNotice.style.cssText = `
        background: var(--warning);
        color: white;
        padding: 0.75rem;
        text-align: center;
        font-size: 0.875rem;
    `;
    header.after(offlineNotice);
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', initApp);
