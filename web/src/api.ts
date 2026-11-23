import type { Report } from "./types";

export class AnalysisError extends Error {
  constructor(
    message: string,
    readonly kind:
      "network" | "limited" | "input" | "response" | "access" = "response",
  ) {
    super(message);
  }
}

export async function getReport(
  url: string,
  body?: unknown,
  accessKey = "",
): Promise<Report> {
  const headers: Record<string, string> = {};
  if (accessKey && url !== "/api/demo")
    headers.Authorization = `Bearer ${accessKey}`;
  if (body !== undefined) headers["Content-Type"] = "application/json";
  const response = await fetch(url, {
    method: body !== undefined ? "POST" : "GET",
    headers,
    ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
  }).catch(() => {
    throw new AnalysisError(
      "Cannot reach CodeImpact. Check your connection or local servers, then retry.",
      "network",
    );
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new AnalysisError(
      typeof data?.detail === "string"
        ? data.detail
        : typeof data?.detail?.message === "string"
          ? data.detail.message
          : `Analysis rejected (${response.status}). Check your snapshot format and limits.`,
      response.status === 401
        ? "access"
        : response.status === 429 ||
            data?.detail?.code === "rate_limited" ||
            data?.detail?.code === "busy"
          ? "limited"
          : response.status === 422 || response.status === 400
            ? "input"
            : "response",
    );
  }
  const report = await response.json().catch(() => {
    throw new AnalysisError(
      "CodeImpact returned an unreadable response. Retry the request, or restart the local API.",
    );
  });
  if (report?.schema_version !== "2.0" && report?.schema_version !== "2.1") {
    throw new Error(
      "Unsupported report version. Restart the API and refresh the dashboard together (schema 2.0 or 2.1 required).",
    );
  }
  return report;
}
