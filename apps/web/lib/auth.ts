export interface User {
  id: string;
  email: string;
  full_name: string;
  is_email_verified: boolean;
  roles: string[];
}

export function saveAuth(token: string, user: User) {
  if (typeof window !== "undefined") {
    localStorage.setItem("mota_access_token", token);
    localStorage.setItem("mota_user", JSON.stringify(user));
  }
}

export function getStoredUser(): User | null {
  if (typeof window === "undefined") return null;
  const userStr = localStorage.getItem("mota_user");
  if (!userStr) return null;
  try {
    return JSON.parse(userStr);
  } catch {
    return null;
  }
}

export function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("mota_access_token");
}

export function clearAuth() {
  if (typeof window !== "undefined") {
    localStorage.removeItem("mota_access_token");
    localStorage.removeItem("mota_user");
  }
}

export function isAuthenticated(): boolean {
  return !!getStoredToken();
}
