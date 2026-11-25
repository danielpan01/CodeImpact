import { open } from "node:fs/promises";
import { test, expect } from "@playwright/test";
import { readFileSync } from "node:fs";
import {
  validateSavedReport,
  readSavedReport,
  maxReportMiB,
} from "../src/saved-report";
import type { Report } from "../src/types";

function fixture(name = "demo"): Report {
  return JSON.parse(
    readFileSync(
      new URL("./quality/fixtures/" + name + ".json", import.meta.url),
      "utf8",
    ),
  );
}

test("accepts complete demo, large, mixed/deleted and empty reports without changing their JSON", () => {
  for (const name of [
    "demo",
    "mixed",
    "large",
    "zero-discovery",
    "unsupported-discovery",
  ]) {
    const report = fixture(name);
    const original = JSON.stringify(report);
    expect(validateSavedReport(report)).toBe(report);
    expect(JSON.stringify(report)).toBe(original);
  }
});

test("rejects oversized files before reading them", async () => {
  let read = false;
  const file = {
    size: maxReportMiB * 1024 * 1024 + 1,
    text: () => {
      read = true;
      return Promise.resolve("{}");
    },
  } as File;
  await expect(readSavedReport(file)).rejects.toThrow(/file limit/);
  expect(read).toBe(false);
});

test("rejects missing fields, duplicate identities, broken paths, evidence and ranges", () => {
  const bad: [string, (r: Report) => void, RegExp][] = [
    ["warnings", (r) => Reflect.deleteProperty(r, "warnings"), /warnings/],
    [
      "stats",
      (r) => Reflect.deleteProperty(r.stats, "elapsed_ms"),
      /statistics/,
    ],
    ["node", (r) => r.nodes.push(r.nodes[0]), /Duplicate ID/],
    ["edge", (r) => r.edges.push(r.edges[0]), /Duplicate ID/],
    [
      "unknown node",
      (r) => {
        r.edges[0].target = "missing";
      },
      /endpoint/,
    ],
    [
      "change",
      (r) => {
        r.changes[0].after = null;
      },
      /revision range/,
    ],
    [
      "absent file",
      (r) => {
        r.source_files[0].before = null;
      },
      /range/,
    ],
    [
      "recommendation",
      (r) => r.recommendations.push(r.recommendations[0]),
      /duplicate recommended/,
    ],
    [
      "direction",
      (r) => r.recommendations[1].evidence_edges.reverse(),
      /caller to dependency/,
    ],
    [
      "distance",
      (r) => {
        r.recommendations[0].distance = 99;
      },
      /distance/,
    ],
    [
      "edge presence",
      (r) => {
        r.edges[0].after = [];
      },
      /Edge revision/,
    ],
    [
      "path presence",
      (r) => {
        r.recommendations[0].path_revision = "after";
      },
      /revision/,
    ],
    [
      "source location",
      (r) => {
        r.edges[0].before[0].location.path = "other.py";
      },
      /endpoint/,
    ],
    [
      "uncaptured before bounds",
      (r) => {
        r.edges[0].before[0].location.end_line = 900;
      },
      /Source range/,
    ],
    [
      "source range",
      (r) => {
        r.changes[0].after!.end_line += 999;
      },
      /Source range/,
    ],
    [
      "reason",
      (r) => {
        r.recommendations[0].reason = "Test itself changed";
      },
      /reason/,
    ],
    [
      "schema",
      (r) => {
        r.edges[0].kind = "fixture";
      },
      /version/,
    ],
  ];
  for (const [name, edit, error] of bad) {
    const report = fixture();
    edit(report);
    expect(() => validateSavedReport(report), name).toThrow(error);
  }
});

test("requires a matching public GitHub PR link and recorded commit IDs", () => {
  const report = fixture();
  report.source = {
    kind: "github_pr",
    repository: "owner/repo",
    head_repository: "fork/repo",
    pr_number: 7,
    pr_url: "https://github.com/owner/repo/pull/7",
    title: "<b>plain text</b>",
    head_sha: "a".repeat(40),
    base_sha: "b".repeat(40),
    merge_base_sha: "c".repeat(40),
    analyzer_version: "0.1.0",
  };
  expect(validateSavedReport(report)).toBe(report);
  for (const url of [
    "javascript:void(0)",
    "https://example.org/",
    "https://github.com/owner/repo/pull/8",
  ]) {
    expect(() =>
      validateSavedReport({
        ...report,
        source: { ...report.source, pr_url: url },
      }),
    ).toThrow(/PR link/);
  }
  report.source.head_sha = "main";
  expect(() => validateSavedReport(report)).toThrow(/revision/);
});

test("an oversized local file leaves the picker ready to retry on desktop and phone", async ({
  page,
}, info) => {
  // A sparse file exercises the native chooser's actual File.size without
  // allocating the payload in the app, the browser driver or the test runner.
  const path = info.outputPath("oversized.json");
  const handle = await open(path, "w");
  try {
    await handle.truncate(maxReportMiB * 1024 * 1024 + 1);
  } finally {
    await handle.close();
  }
  await page.goto("/");
  await page.getByLabel("Saved report JSON").setInputFiles(path);
  await expect(page.getByRole("alert")).toContainText("96 MiB file limit");
  await expect(
    page.getByRole("button", { name: "Open saved report" }),
  ).toBeFocused();
  await page.getByLabel("Saved report JSON").setInputFiles({
    name: "valid.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(fixture())),
  });
  await expect(page.locator(".test-row")).toHaveCount(3);
});
