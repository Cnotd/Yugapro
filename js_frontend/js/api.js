/**
 * Yoga Assessment API Client
 * JavaScript API wrapper for Python Flask backend
 */

class YogaAPI {
    constructor(baseUrl = 'http://localhost:5000/api') {
        this.baseUrl = baseUrl;
        this.storageKey = 'yoga_auth_session';
        this.accessToken = null;
        this.refreshToken = null;
        this.expiresAt = 0;
        this.refreshExpiresAt = 0;
        this.user = null;
        this.loadSession();
        console.log('[YogaAPI] Initialized with baseUrl:', baseUrl);
    }

    loadSession() {
        const raw = localStorage.getItem(this.storageKey);
        if (!raw) {
            return false;
        }

        try {
            const session = JSON.parse(raw);
            this.accessToken = session.access_token || null;
            this.refreshToken = session.refresh_token || null;
            this.expiresAt = session.expires_at || 0;
            this.refreshExpiresAt = session.refresh_expires_at || 0;
            this.user = session.user || null;

            if (this.refreshExpiresAt && Date.now() >= this.refreshExpiresAt) {
                this.clearSession();
                return false;
            }

            return true;
        } catch (error) {
            this.clearSession();
            return false;
        }
    }

    saveSession({ access_token, refresh_token, expires_in, refresh_expires_in, user }) {
        this.accessToken = access_token;
        this.refreshToken = refresh_token;
        this.expiresAt = Date.now() + (expires_in * 1000);
        this.refreshExpiresAt = Date.now() + (refresh_expires_in * 1000);
        this.user = user || this.user;

        localStorage.setItem(this.storageKey, JSON.stringify({
            access_token: this.accessToken,
            refresh_token: this.refreshToken,
            expires_at: this.expiresAt,
            refresh_expires_at: this.refreshExpiresAt,
            user: this.user
        }));
    }

    clearSession() {
        this.accessToken = null;
        this.refreshToken = null;
        this.expiresAt = 0;
        this.refreshExpiresAt = 0;
        this.user = null;
        localStorage.removeItem(this.storageKey);
    }

    isAuthenticated() {
        return !!this.user && !!this.accessToken;
    }

    async ensureAccessToken() {
        if (!this.accessToken) {
            return false;
        }

        if (Date.now() >= this.expiresAt - 30000) {
            return await this.refreshTokenIfNeeded();
        }

        return true;
    }

    async refreshTokenIfNeeded() {
        if (!this.refreshToken) {
            this.clearSession();
            return false;
        }

        if (Date.now() >= this.refreshExpiresAt) {
            this.clearSession();
            return false;
        }

        try {
            const response = await fetch(`${this.baseUrl}/auth/refresh`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ refresh_token: this.refreshToken })
            });

            if (!response.ok) {
                this.clearSession();
                return false;
            }

            const data = await response.json();
            this.saveSession({
                access_token: data.access_token,
                refresh_token: data.refresh_token,
                expires_in: data.expires_in,
                refresh_expires_in: data.refresh_expires_in,
                user: this.user
            });
            return true;
        } catch (error) {
            this.clearSession();
            return false;
        }
    }

    async authFetch(path, options = {}) {
        const url = `${this.baseUrl}${path}`;
        const isAuthRoute = path.startsWith('/auth/');

        if (!isAuthRoute) {
            const ok = await this.ensureAccessToken();
            if (!ok) {
                throw new Error('Unauthorized');
            }
        }

        const headers = new Headers(options.headers || {});

        if (!options.body || !(options.body instanceof FormData)) {
            headers.set('Content-Type', 'application/json');
        }

        if (!isAuthRoute && this.accessToken) {
            headers.set('Authorization', `Bearer ${this.accessToken}`);
        }

        const response = await fetch(url, {
            ...options,
            headers,
        });

        if (response.status === 401 && !isAuthRoute) {
            const refreshed = await this.refreshTokenIfNeeded();
            if (refreshed) {
                if (this.accessToken) {
                    headers.set('Authorization', `Bearer ${this.accessToken}`);
                }
                const retryResponse = await fetch(url, {
                    ...options,
                    headers,
                });
                if (!retryResponse.ok) {
                    throw await this.createRequestError(retryResponse, 'Request failed');
                }
                return retryResponse;
            }
        }

        if (!response.ok) {
            throw await this.createRequestError(response, 'Request failed');
        }

        return response;
    }

    async createRequestError(response, fallbackMessage = 'Request failed') {
        const payload = await response.json().catch(() => null);
        return new Error((payload && payload.error) || response.statusText || fallbackMessage);
    }

    async healthCheck() {
        const response = await fetch(`${this.baseUrl}/health`);
        if (!response.ok) {
            throw new Error('API is not available');
        }
        return response.json();
    }

    async getStats() {
        const response = await fetch(`${this.baseUrl}/stats`);
        if (!response.ok) {
            throw new Error('Failed to fetch stats');
        }
        return response.json();
    }

    async getPoseStandards() {
        const response = await fetch(`${this.baseUrl}/pose/standards`);
        if (!response.ok) {
            throw new Error('Failed to fetch pose standards');
        }
        return response.json();
    }

    async uploadVideo(file, poseName = '下犬式') {
        const formData = new FormData();
        formData.append('video', file);
        formData.append('pose_name', poseName);

        const response = await this.authFetch('/assessment/upload', {
            method: 'POST',
            body: formData,
            headers: {} // Content-Type will be handled automatically
        });

        return response.json();
    }

    async getAssessment(assessmentId) {
        const response = await this.authFetch(`/assessment/${assessmentId}`);
        return response.json();
    }

    async getAssessmentResult(assessmentId) {
        const response = await this.authFetch(`/assessment/${assessmentId}/result`);
        return response.json();
    }

    async getUserAssessments(limit = 50, offset = 0) {
        const response = await this.authFetch(`/user/assessments?limit=${limit}&offset=${offset}`);
        return response.json();
    }

    async getUsers(limit = 100, offset = 0) {
        const response = await this.authFetch(`/users?limit=${limit}&offset=${offset}`);
        return response.json();
    }

    async createUser(username, password, email, role = 'learner') {
        const response = await this.authFetch('/users', {
            method: 'POST',
            body: JSON.stringify({ username, password, email, role })
        });
        return response.json();
    }

    async updateUser(userId, role, isActive) {
        const payload = {};
        if (role) payload.role = role;
        if (typeof isActive === 'boolean') payload.is_active = isActive;

        const response = await this.authFetch(`/users/${userId}`, {
            method: 'PUT',
            body: JSON.stringify(payload)
        });
        return response.json();
    }

    async getProfile() {
        const response = await this.authFetch('/auth/me');
        return response.json();
    }

    async login(username, password) {
        const response = await fetch(`${this.baseUrl}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });

        if (!response.ok) {
            const message = await response.json().catch(() => null);
            throw new Error((message && message.error) || '登录失败');
        }

        const data = await response.json();
        this.saveSession({
            access_token: data.access_token,
            refresh_token: data.refresh_token,
            expires_in: data.expires_in,
            refresh_expires_in: data.refresh_expires_in,
            user: data.user
        });
        return data.user;
    }

    async register(username, password, email) {
        const response = await fetch(`${this.baseUrl}/auth/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password, email })
        });

        if (!response.ok) {
            const message = await response.json().catch(() => null);
            throw new Error((message && message.error) || '注册失败');
        }

        const data = await response.json();
        this.saveSession({
            access_token: data.access_token,
            refresh_token: data.refresh_token,
            expires_in: data.expires_in,
            refresh_expires_in: data.refresh_expires_in,
            user: data.user
        });
        return data.user;
    }

    async logout() {
        const response = await this.authFetch('/auth/logout', {
            method: 'POST',
            body: JSON.stringify({ refresh_token: this.refreshToken })
        });
        if (!response.ok) {
            throw new Error('Logout failed');
        }
        this.clearSession();
        return response.json();
    }

    async pollAssessment(assessmentId, onProgress = null, maxAttempts = 300) {
        for (let i = 0; i < maxAttempts; i++) {
            const status = await this.getAssessment(assessmentId);
            if (onProgress) {
                onProgress(status);
            }
            if (status.status === 'completed') {
                return status.result;
            }
            if (status.status === 'failed') {
                throw new Error((status.result && status.result.error) || status.error || 'Assessment failed');
            }
            await new Promise(resolve => setTimeout(resolve, 1000));
        }
        throw new Error('Assessment timeout');
    }
}

window.YogaAPI = YogaAPI;
