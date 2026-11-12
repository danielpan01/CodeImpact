import type { Report } from "./types";

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
    throw new Error(
      "Cannot reach CodeImpact. Start the local servers, then retry.",
    );
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(
      typeof data.detail === "string"
        ? data.detail
        : typeof data.detail?.message === "string"
          ? data.detail.message
          : `Analysis rejected (${response.status}). Check your snapshot format and limits.`,
    );
  }
  const report = await response.json();
  if (report.schema_version !== "2.0") {
    throw new Error(
      "Unsupported report version. Restart the API and refresh the dashboard together (schema 2.0 required).",
    );
  }
  return report;
}
