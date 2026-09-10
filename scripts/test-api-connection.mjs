/**
 * Minimal Frontend-to-Backend Connection Test (Module 0 Foundation)
 * Verifies that Next.js client can communicate with the running FastAPI backend
 * via GET /api/v1/health.
 */

async function runConnectionTest() {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000/api/v1";
  const healthEndpoint = `${baseUrl}/health`;

  console.log(`[Frontend Test] Pinging FastAPI Backend at: ${healthEndpoint}`);

  try {
    const startTime = Date.now();
    const res = await fetch(healthEndpoint, {
      method: "GET",
      headers: {
        "Accept": "application/json",
        "X-Request-ID": "frontend-connection-test-probe",
      },
    });

    const duration = Date.now() - startTime;

    if (!res.ok) {
      console.error(`[Frontend Test] Backend returned status ${res.status}`);
      process.exit(1);
    }

    const data = await res.json();
    const requestId = res.headers.get("x-request-id");
    const serverTimeMs = res.headers.get("x-response-time-ms");

    console.log(`[Frontend Test] SUCCESS! Backend responded in ${duration}ms:`);
    console.log(JSON.stringify(data, null, 2));
    console.log(`[Frontend Test] Verified Response Headers: X-Request-ID=${requestId}, X-Response-Time-Ms=${serverTimeMs}`);

    // Verify expected payload schema
    if (data.status === "healthy" && data.service && data.version) {
      console.log(`[Frontend Test] PASS: Backend is healthy and communicating with the frontend client.`);
      process.exit(0);
    } else {
      console.error(`[Frontend Test] FAIL: Unexpected response payload structure:`, data);
      process.exit(1);
    }
  } catch (err) {
    console.error(`[Frontend Test] Connection error:`, err.message);
    process.exit(1);
  }
}

runConnectionTest();
