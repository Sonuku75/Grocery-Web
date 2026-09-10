/**
 * Cartify Centralized API Client (Module 0 Foundation)
 * 
 * Features:
 * - Base URL configuration from NEXT_PUBLIC_API_BASE_URL
 * - Strict timeout handling via AbortController
 * - Unified error handling & ApiError hierarchy
 * - Token management hooks (prepared for Module 1 Auth)
 * - Safe retry strategy for idempotent requests
 * - Zero secret leakage to the browser
 */

import { ApiError, NetworkError, TimeoutError, UnauthorizedError } from "./errors";

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  error?: string;
  code?: string;
  requestId?: string;
}

export interface RequestOptions extends Omit<RequestInit, "body"> {
  body?: unknown;
  params?: Record<string, string | number | boolean | undefined | null>;
  timeoutMs?: number;
  retries?: number;
  skipAuth?: boolean;
}

const DEFAULT_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";
const DEFAULT_TIMEOUT_MS = 10000;

export class ApiClient {
  private baseUrl: string;
  private defaultTimeout: number;
  private onUnauthorizedCallback: (() => void) | null = null;

  constructor(baseUrl: string = DEFAULT_BASE_URL, defaultTimeout: number = DEFAULT_TIMEOUT_MS) {
    // Strip trailing slash if present
    this.baseUrl = baseUrl.replace(/\/+$/, "");
    this.defaultTimeout = defaultTimeout;
  }

  /**
   * Token storage hooks - prepared for Module 1 Authentication
   */
  public getAccessToken(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem("cartify_access_token");
  }

  public setAccessToken(token: string | null): void {
    if (typeof window === "undefined") return;
    if (token) {
      localStorage.setItem("cartify_access_token", token);
    } else {
      localStorage.removeItem("cartify_access_token");
    }
  }

  public getToken(): string | null {
    return this.getAccessToken();
  }

  public setToken(token: string | null): void {
    this.setAccessToken(token);
  }

  public getRefreshToken(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem("cartify_refresh_token");
  }

  public setRefreshToken(token: string | null): void {
    if (typeof window === "undefined") return;
    if (token) {
      localStorage.setItem("cartify_refresh_token", token);
    } else {
      localStorage.removeItem("cartify_refresh_token");
    }
  }

  public clearTokens(): void {
    if (typeof window === "undefined") return;
    localStorage.removeItem("cartify_access_token");
    localStorage.removeItem("cartify_refresh_token");
    localStorage.removeItem("cartify_user");
  }

  public onUnauthorized(callback: () => void): void {
    this.onUnauthorizedCallback = callback;
  }

  /**
   * Builds full URL with normalized query parameters
   */
  private buildUrl(endpoint: string, params?: RequestOptions["params"]): string {
    const cleanEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
    const url = new URL(`${this.baseUrl}${cleanEndpoint}`);

    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          url.searchParams.append(key, String(value));
        }
      });
    }

    return url.toString();
  }

  /**
   * Core request execution with timeout and response normalization
   */
  public async request<T>(endpoint: string, options: RequestOptions = {}): Promise<ApiResponse<T>> {
    const {
      params,
      headers = {},
      body,
      timeoutMs = this.defaultTimeout,
      retries = 0,
      skipAuth = false,
      method = "GET",
      ...customConfig
    } = options;

    const fullUrl = this.buildUrl(endpoint, params);
    const isSafeMethod = method === "GET" || method === "HEAD" || method === "OPTIONS";
    const allowedRetries = isSafeMethod ? retries : 0;

    let attempts = 0;
    while (attempts <= allowedRetries) {
      attempts++;

      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), timeoutMs);

      const requestHeaders: Record<string, string> = {
        Accept: "application/json",
        ...((headers as Record<string, string>) || {}),
      };

      if (body !== undefined && !(body instanceof FormData)) {
        requestHeaders["Content-Type"] = "application/json";
      }

      if (!skipAuth) {
        const token = this.getAccessToken();
        if (token) {
          requestHeaders["Authorization"] = `Bearer ${token}`;
        }
      }

      try {
        const response = await fetch(fullUrl, {
          ...customConfig,
          method,
          headers: requestHeaders,
          body: body !== undefined ? (body instanceof FormData ? body : JSON.stringify(body)) : undefined,
          signal: controller.signal,
        });

        clearTimeout(timer);

        const requestId = response.headers.get("X-Request-ID") || undefined;

        // Handle 401 Unauthorized
        if (response.status === 401) {
          this.clearTokens();
          if (this.onUnauthorizedCallback) {
            this.onUnauthorizedCallback();
          }
          throw new UnauthorizedError("Session expired or unauthorized.", undefined, requestId);
        }

        // Parse JSON response body
        let jsonPayload: any = null;
        const contentType = response.headers.get("content-type") || "";
        if (contentType.includes("application/json")) {
          jsonPayload = await response.json().catch(() => null);
        }

        if (!response.ok) {
          const errorMessage =
            jsonPayload?.error?.message ||
            jsonPayload?.error ||
            jsonPayload?.detail ||
            `Request failed with status ${response.status}`;
          const errorCode = jsonPayload?.error?.code || jsonPayload?.code || `HTTP_${response.status}`;

          throw new ApiError(response.status, errorMessage, errorCode, jsonPayload?.error?.details, requestId);
        }

        // Return standardized successful envelope
        const unwrappedData: T =
          jsonPayload !== null && jsonPayload !== undefined
            ? jsonPayload.data !== undefined
              ? jsonPayload.data
              : jsonPayload
            : (null as unknown as T);

        return {
          success: true,
          data: unwrappedData,
          message: jsonPayload?.message,
          requestId,
        };
      } catch (err: unknown) {
        clearTimeout(timer);

        // AbortController timeout
        if (err instanceof DOMException && err.name === "AbortError") {
          if (attempts <= allowedRetries) continue;
          return {
            success: false,
            data: null as unknown as T,
            error: `Request timed out after ${timeoutMs}ms.`,
            code: "TIMEOUT_ERROR",
          };
        }

        if (ApiError.isApiError(err)) {
          // If 5xx error and retries remain for safe method, retry
          if (err.status >= 500 && attempts <= allowedRetries) {
            await new Promise((resolve) => setTimeout(resolve, 300 * attempts));
            continue;
          }
          return {
            success: false,
            data: null as unknown as T,
            error: err.message,
            code: err.code,
            requestId: err.requestId,
          };
        }

        // Network or fetch failure
        if (attempts <= allowedRetries) {
          await new Promise((resolve) => setTimeout(resolve, 300 * attempts));
          continue;
        }

        const networkErr = new NetworkError(err instanceof Error ? err.message : "Network request failed.");
        return {
          success: false,
          data: null as unknown as T,
          error: networkErr.message,
          code: networkErr.code,
        };
      }
    }

    return {
      success: false,
      data: null as unknown as T,
      error: "Max retries exceeded.",
      code: "MAX_RETRIES_EXCEEDED",
    };
  }

  public get<T>(endpoint: string, options?: RequestOptions): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...options, method: "GET" });
  }

  public post<T>(endpoint: string, body?: unknown, options?: RequestOptions): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...options, method: "POST", body });
  }

  public put<T>(endpoint: string, body?: unknown, options?: RequestOptions): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...options, method: "PUT", body });
  }

  public patch<T>(endpoint: string, body?: unknown, options?: RequestOptions): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...options, method: "PATCH", body });
  }

  public delete<T>(endpoint: string, options?: RequestOptions): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...options, method: "DELETE" });
  }
}

/**
 * Singleton API Client Instance
 */
export const apiClient = new ApiClient();

/**
 * Mock data toggle for local development without backend
 */
export function isMockMode(): boolean {
  return process.env.NEXT_PUBLIC_USE_MOCK !== "false";
}
