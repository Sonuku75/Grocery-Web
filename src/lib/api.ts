import { ApiResponse } from "@/types";

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api";

interface RequestOptions extends RequestInit {
  params?: Record<string, string | number | boolean | undefined>;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private getToken(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem("cartify_access_token");
  }

  public setToken(token: string | null) {
    if (typeof window === "undefined") return;
    if (token) {
      localStorage.setItem("cartify_access_token", token);
    } else {
      localStorage.removeItem("cartify_access_token");
    }
  }

  public async request<T>(endpoint: string, options: RequestOptions = {}): Promise<ApiResponse<T>> {
    const { params, headers = {}, ...customConfig } = options;

    let url = `${this.baseUrl}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`;
    if (params) {
      const searchParams = new URLSearchParams();
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          searchParams.append(key, String(value));
        }
      });
      const queryString = searchParams.toString();
      if (queryString) {
        url += `?${queryString}`;
      }
    }

    const token = this.getToken();
    const defaultHeaders: Record<string, string> = {
      "Content-Type": "application/json",
      Accept: "application/json",
    };

    if (token) {
      defaultHeaders["Authorization"] = `Bearer ${token}`;
    }

    try {
      const response = await fetch(url, {
        ...customConfig,
        headers: {
          ...defaultHeaders,
          ...headers,
        },
      });

      if (response.status === 401) {
        // Token expired or invalid
        if (typeof window !== "undefined") {
          localStorage.removeItem("cartify_access_token");
          localStorage.removeItem("cartify_user");
        }
      }

      const data = await response.json();

      if (!response.ok) {
        return {
          success: false,
          data: null as unknown as T,
          error: data.detail || data.message || `Request failed with status ${response.status}`,
        };
      }

      return {
        success: true,
        data: data.data !== undefined ? data.data : data,
        message: data.message,
      };
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Network request failed";
      return {
        success: false,
        data: null as unknown as T,
        error: message,
      };
    }
  }

  public get<T>(endpoint: string, options?: RequestOptions): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...options, method: "GET" });
  }

  public post<T>(endpoint: string, body?: unknown, options?: RequestOptions): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      ...options,
      method: "POST",
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  public put<T>(endpoint: string, body?: unknown, options?: RequestOptions): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      ...options,
      method: "PUT",
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  public delete<T>(endpoint: string, options?: RequestOptions): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...options, method: "DELETE" });
  }
}

export const apiClient = new ApiClient(BASE_URL);
