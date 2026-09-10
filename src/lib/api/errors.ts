/**
 * Cartify API Error Types and Utilities
 * Standardizes API error responses across the Next.js frontend application.
 */

export interface ApiErrorPayload {
  code: string;
  message: string;
  details?: unknown;
  requestId?: string;
}

export class ApiError extends Error {
  public readonly status: number;
  public readonly code: string;
  public readonly details?: unknown;
  public readonly requestId?: string;

  constructor(status: number, message: string, code = "API_ERROR", details?: unknown, requestId?: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
    this.requestId = requestId;

    // Maintain prototype chain
    Object.setPrototypeOf(this, ApiError.prototype);
  }

  public static isApiError(err: unknown): err is ApiError {
    return err instanceof ApiError;
  }
}

export class NetworkError extends ApiError {
  constructor(message = "Network connection failed. Please check your internet connection.", details?: unknown) {
    super(0, message, "NETWORK_ERROR", details);
    this.name = "NetworkError";
    Object.setPrototypeOf(this, NetworkError.prototype);
  }
}

export class TimeoutError extends ApiError {
  constructor(timeoutMs: number) {
    super(408, `Request timed out after ${timeoutMs}ms.`, "TIMEOUT_ERROR");
    this.name = "TimeoutError";
    Object.setPrototypeOf(this, TimeoutError.prototype);
  }
}

export class UnauthorizedError extends ApiError {
  constructor(message = "Session expired or unauthorized. Please log in again.", details?: unknown, requestId?: string) {
    super(401, message, "UNAUTHORIZED", details, requestId);
    this.name = "UnauthorizedError";
    Object.setPrototypeOf(this, UnauthorizedError.prototype);
  }
}
