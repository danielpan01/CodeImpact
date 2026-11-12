import type { Report } from "./types";

export class AnalysisError extends Error {
  constructor(
    message: string,
    readonly kind: "network" | "limited" | "input" | "response" = "response",
  ) {
    super(message);
  }
}

export async function getReport(url: string, body?: unknown): Promise<Report> {
  const response = await fetch(
    url,
    body !== undefined
      ? {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        }
      : {},
  ).catch(() => {
    throw new AnalysisError(
      "Cannot reach CodeImpact. Start the local servers, then retry.",
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
      response.status === 429 || data?.detail?.code === "rate_limited"
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
  if (report?.schema_version !== "2.0") {
    throw new Error(
      "Unsupported report version. Restart the API and refresh the dashboard together (schema 2.0 required).",
    );
  }
  return report;
}
