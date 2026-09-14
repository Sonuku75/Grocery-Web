/**
 * Cartify URL Security Utilities (Module 15.4)
 * 
 * Provides defense against Open Redirect attacks, protocol manipulation,
 * and malicious URI schemes in frontend navigation.
 */

/**
 * Validates and sanitizes redirect destinations to prevent Open Redirect vulnerabilities.
 * Only relative internal application paths beginning with a single '/' are permitted.
 * 
 * Specifically rejects:
 * - Protocol-relative URLs: '//attacker.example' or '/\\attacker.example'
 * - External absolute URLs: 'https://attacker.example' or 'http://attacker.example'
 * - Dangerous pseudo-schemes: 'javascript:...', 'data:...', 'vbscript:...'
 * - Backslashes (which some browsers treat as slashes in authority parsing)
 * - CRLF and non-printable control characters
 * 
 * @param target The untrusted redirect destination string (e.g. from searchParams)
 * @param fallback Safe internal fallback destination (default: '/profile')
 * @returns Safe sanitized path
 */
export function getSafeRedirect(
  target: string | null | undefined,
  fallback: string = "/profile"
): string {
  if (!target || typeof target !== "string") {
    return fallback;
  }

  const trimmed = target.trim();

  // Must begin with '/' and NOT with '//' or '/\'
  if (!trimmed.startsWith("/") || trimmed.startsWith("//") || trimmed.startsWith("/\\")) {
    return fallback;
  }

  // Reject any backslashes
  if (trimmed.includes("\\")) {
    return fallback;
  }

  // Extract path component before query and fragment
  const pathComponent = trimmed.split("?")[0].split("#")[0];

  // In a valid relative URL path, there must not be a colon before the query string
  if (pathComponent.includes(":")) {
    return fallback;
  }

  // Check for control characters or line terminators (CRLF)
  if (/[\x00-\x1F\x7F]/.test(trimmed)) {
    return fallback;
  }

  return trimmed;
}
