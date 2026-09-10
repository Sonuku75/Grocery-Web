/**
 * Backend Health Verification Service (Module 0 Foundation)
 * Validates connectivity from the Next.js frontend to the Python FastAPI backend.
 */

import { apiClient, ApiResponse } from "./client";

export interface BackendHealthResponse {
  status: string;
  service: string;
  version: string;
  timestamp: string;
}

export interface BackendReadinessResponse {
  status: string;
  services: {
    postgres_primary: string;
    postgres_replica: string;
    redis: string;
  };
}

/**
 * Pings the FastAPI liveness endpoint: GET /api/v1/health
 */
export async function checkBackendHealth(): Promise<ApiResponse<BackendHealthResponse>> {
  return apiClient.get<BackendHealthResponse>("/health", {
    timeoutMs: 5000,
    skipAuth: true,
  });
}

/**
 * Checks the FastAPI readiness endpoint: GET /api/v1/ready
 */
export async function checkBackendReadiness(): Promise<ApiResponse<BackendReadinessResponse>> {
  return apiClient.get<BackendReadinessResponse>("/ready", {
    timeoutMs: 5000,
    skipAuth: true,
  });
}
