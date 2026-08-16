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

  async request(path: string, options: RequestInit = {}) {
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
    return this.request("/api/v1/auth/me");
  }

  // Public
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

  // Hermes & Fábricas Adicionais
  async getHermesStatus(sessionId: string) {
    return this.request(`/api/v1/hermes/pipeline/status/${sessionId}`);
  }

  async getPostizStatus() {
    return this.request("/api/v1/postiz/status");
  }

  async getDeliverableApps() {
    return this.request("/api/v1/deliverables");
  }
}

export const api = new ApiClient();

