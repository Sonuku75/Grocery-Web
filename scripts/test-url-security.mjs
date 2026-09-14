/**
 * Open Redirect and URL Security Verification Script
 * Validates getSafeRedirect behavior against standard OWASP and CWE-601 vectors.
 */

import assert from "node:assert";

// Implement same logic as in urlSecurity.ts for standalone verification
function getSafeRedirect(target, fallback = "/profile") {
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

const testCases = [
  // Malicious attack vectors -> MUST return fallback (/profile)
  { input: "//attacker.com", expected: "/profile", desc: "Protocol-relative URL" },
  { input: "/\\attacker.com", expected: "/profile", desc: "Backslash protocol bypass" },
  { input: "https://evil.com/phish", expected: "/profile", desc: "Absolute HTTPS URL" },
  { input: "http://evil.com/phish", expected: "/profile", desc: "Absolute HTTP URL" },
  { input: "javascript:alert(document.cookie)", expected: "/profile", desc: "JavaScript scheme" },
  { input: "data:text/html;base64,PHNjcmlwdD4=", expected: "/profile", desc: "Data URI scheme" },
  { input: "vbscript:msgbox(1)", expected: "/profile", desc: "VBScript scheme" },
  { input: "/account\r\nSet-Cookie:admin=1", expected: "/profile", desc: "CRLF header injection" },
  { input: "/account\nevil:true", expected: "/profile", desc: "Newline injection" },
  { input: "\\evil.com", expected: "/profile", desc: "Windows path backslash" },
  { input: "/orders/..\\..\\evil", expected: "/profile", desc: "Path traversal with backslash" },
  { input: "", expected: "/profile", desc: "Empty string" },
  { input: null, expected: "/profile", desc: "Null input" },
  { input: undefined, expected: "/profile", desc: "Undefined input" },

  // Legitimate internal paths -> MUST be permitted
  { input: "/account", expected: "/account", desc: "Simple internal route" },
  { input: "/account/security", expected: "/account/security", desc: "Nested internal route" },
  { input: "/account/sessions", expected: "/account/sessions", desc: "Sessions route" },
  { input: "/orders/ord-12345", expected: "/orders/ord-12345", desc: "Dynamic route with ID" },
  { input: "/search?q=organic+milk&category=dairy", expected: "/search?q=organic+milk&category=dairy", desc: "Path with query string" },
  { input: "/checkout#payment-section", expected: "/checkout#payment-section", desc: "Path with fragment" },
];

let passed = 0;
for (const tc of testCases) {
  const result = getSafeRedirect(tc.input, "/profile");
  assert.strictEqual(
    result,
    tc.expected,
    `FAILED: ${tc.desc} - input: "${tc.input}", got: "${result}", expected: "${tc.expected}"`
  );
  passed++;
  console.log(`  ✓ PASSED: ${tc.desc}`);
}

console.log(`\nAll ${passed} Open Redirect tests passed successfully!`);
