const API_URL = process.env.NEXT_PUBLIC_API_URL || "";

class ApiClient {
  private token: string | null = null;

  setToken(token: string | null) {
    this.token = token;
    if (token) {
      localStorage.setItem("dz_token", token);
    } else {
      localStorage.removeItem("dz_token");
    }
  }

  getToken(): string | null {
    if (typeof window !== "undefined" && !this.token) {
      this.token = localStorage.getItem("dz_token");
    }
    return this.token;
  }

  private async request(path: string, options: RequestInit = {}) {
    const token = this.getToken();
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(options.headers as Record<string, string> || {}),
    };
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    const res = await fetch(`${API_URL}${path}`, { ...options, headers });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Erro desconhecido" }));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return res.json();
  }

  // Auth
  async register(email: string, name: string, password: string) {
    const data = await this.request("/api/v1/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, name, password }),
    });
    this.setToken(data.token);
    return data;
  }

  async login(email: string, password: string) {
    const data = await this.request("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    this.setToken(data.token);
    return data;
  }

  async googleLogin(google_id: string, email: string, name: string, avatar_url?: string) {
    const data = await this.request("/api/v1/auth/google", {
      method: "POST",
      body: JSON.stringify({ google_id, email, name, avatar_url }),
    });
    this.setToken(data.token);
    return data;
  }

  async forgotPassword(email: string) {
    return this.request("/api/v1/auth/forgot-password", {
      method: "POST",
      body: JSON.stringify({ email }),
    });
  }

  async resetPassword(token: string, new_password: string) {
    return this.request("/api/v1/auth/reset-password", {
      method: "POST",
      body: JSON.stringify({ token, new_password }),
    });
  }

  async getMe() {
    return this.request("/api/v1/auth/me");
  }

  async logout() {
    await this.request("/api/v1/auth/logout", { method: "POST" });
    this.setToken(null);
  }

  // Member
  async getDashboard() {
    return this.request("/api/v1/member/dashboard");
  }

  async getMemberCourses() {
    return this.request("/api/v1/member/courses");
  }

  async enrollCourse(courseId: string) {
    return this.request(`/api/v1/member/courses/${courseId}/enroll`, { method: "POST", body: "{}" });
  }

  async completeLesson(lessonId: string, trackId: string, scorePct?: number) {
    return this.request(`/api/v1/member/lessons/${lessonId}/complete`, {
      method: "POST",
      body: JSON.stringify({ track_id: trackId, score_pct: scorePct }),
    });
  }

  async getPoints() {
    return this.request("/api/v1/member/points");
  }

  async getBadges() {
    return this.request("/api/v1/member/badges");
  }

  async getStreak() {
    return this.request("/api/v1/member/streak");
  }

  // Public
  async getRanking() {
    return this.request("/api/v1/ranking");
  }

  async getCombos() {
    return this.request("/api/v1/combos");
  }

  async getCombo(slug: string) {
    return this.request(`/api/v1/combos/${slug}`);
  }

  async getCourses() {
    return this.request("/api/v1/courses");
  }

  async getBooks() {
    return this.request("/api/v1/books");
  }

  // Admin
  async getAdminUsers() {
    return this.request("/api/v1/admin/users");
  }

  async getAdminStats() {
    return this.request("/api/v1/admin/stats");
  }

  async createCombo(data: any) {
    return this.request("/api/v1/combos", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async deleteCombo(comboId: string) {
    return this.request(`/api/v1/admin/combos/${comboId}`, { method: "DELETE" });
  }

  // Admin — Course Factory Pipeline
  async runCourseFactory(data: { topic: string; course_title?: string; difficulty?: string; price_cents?: number; target_modules?: number; lessons_per_module?: number }) {
    return this.request("/api/v1/pipeline/run-course-factory", {
      method: "POST", body: JSON.stringify(data),
    });
  }

  async getCourseFactoryStatus(taskId: string) {
    return this.request(`/api/v1/pipeline/course-factory/status/${taskId}`);
  }

  async getCourseFactoryHistory() {
    return this.request("/api/v1/pipeline/course-factory/history");
  }

  // Admin — Courses CRUD
  async adminListCourses() {
    return this.request("/api/v1/admin/courses");
  }

  async adminCreateCourse(data: { title: string; topic?: string; description?: string; difficulty?: string; price_cents?: number }) {
    return this.request("/api/v1/admin/courses", {
      method: "POST", body: JSON.stringify(data),
    });
  }

  async adminGetCourse(courseId: string) {
    return this.request(`/api/v1/admin/courses/${courseId}`);
  }

  async adminUpdateCourse(courseId: string, data: any) {
    return this.request(`/api/v1/admin/courses/${courseId}`, {
      method: "PUT", body: JSON.stringify(data),
    });
  }

  async adminDeleteCourse(courseId: string) {
    return this.request(`/api/v1/admin/courses/${courseId}`, { method: "DELETE" });
  }

  async adminPublishCourse(courseId: string) {
    return this.request(`/api/v1/admin/courses/${courseId}/publish`, { method: "POST", body: "{}" });
  }

  async adminUnpublishCourse(courseId: string) {
    return this.request(`/api/v1/admin/courses/${courseId}/unpublish`, { method: "POST", body: "{}" });
  }

  // Admin — Learning Paths
  async adminListLearningPaths() {
    return this.request("/api/v1/admin/learning-paths");
  }

  async adminCreateLearningPath(data: { title: string; slug: string; description?: string }) {
    return this.request("/api/v1/admin/learning-paths", {
      method: "POST", body: JSON.stringify(data),
    });
  }

  async adminGetLearningPath(pathId: string) {
    return this.request(`/api/v1/admin/learning-paths/${pathId}`);
  }

  async adminUpdateLearningPath(pathId: string, data: any) {
    return this.request(`/api/v1/admin/learning-paths/${pathId}`, {
      method: "PUT", body: JSON.stringify(data),
    });
  }

  async adminDeleteLearningPath(pathId: string) {
    return this.request(`/api/v1/admin/learning-paths/${pathId}`, { method: "DELETE" });
  }

  async adminAddCourseToPath(pathId: string, courseId: string, order: number = 1) {
    return this.request(`/api/v1/admin/learning-paths/${pathId}/courses`, {
      method: "POST", body: JSON.stringify({ course_id: courseId, order }),
    });
  }

  async adminRemoveCourseFromPath(pathId: string, courseId: string) {
    return this.request(`/api/v1/admin/learning-paths/${pathId}/courses/${courseId}`, { method: "DELETE" });
  }

  // Admin — Analytics
  async adminAnalyticsOverview() {
    return this.request("/api/v1/admin/analytics/overview");
  }

  async adminAnalyticsCourses() {
    return this.request("/api/v1/admin/analytics/courses");
  }
}

export const api = new ApiClient();
