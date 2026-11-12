import { Icon } from "./Icon";
import { colorSource } from "./source-tokens";
import type {
  Report,
  SourceRange,
  SourceRevision,
  SymbolChange,
} from "./types";

// Bound DOM size and individual long lines independently of the snapshot limits.
const MAX_LINES = 120;
const MAX_CHARACTERS = 12_000;
const MAX_LINE_CHARACTERS = 500;

function SourcePane({
  label,
  source,
  range,
}: {
  label: string;
  source: SourceRevision | null;
  range: SourceRange | null;
}) {
  const lines = source?.text.replace(/\r\n?/g, "\n").split("\n") ?? [];
  if (lines.at(-1) === "") lines.pop();
  const start = range?.line ?? 1;
  const end = range?.end_line ?? lines.length;
  const canShow = range !== null || source?.parse_status === "unparseable";
  const available = canShow ? lines.slice(start - 1, end) : [];
  let remaining = MAX_CHARACTERS;
  let truncated = available.length > MAX_LINES;
  const preview: { number: number; text: string; clipped: boolean }[] = [];
  for (const [i, text] of available.slice(0, MAX_LINES).entries()) {
    if (remaining === 0) {
      truncated = true;
      break;
    }
    // Reserve one character for the newline rendered after each source line.
    const shown = text.slice(0, Math.min(MAX_LINE_CHARACTERS, remaining - 1));
    remaining -= shown.length + 1;
    const clipped = shown.length < text.length;
    truncated ||= clipped;
    preview.push({ number: start + i, text: shown, clipped });
  }
  const colored = colorSource(preview.map((line) => line.text));
  return (
    <section className="source-pane" aria-label={`${label} source`}>
      <h4>
        {label} <small>{range ? `lines ${start}–${end}` : ""}</small>
      </h4>
      {!source ? (
        <p>File absent in this revision.</p>
      ) : source.text === "" ? (
        <p>Empty file (present in this revision).</p>
      ) : (
        <>
          {source.parse_status === "unparseable" && (
            <p className="source-warning">
              Could not parse this revision. Showing raw source; definitions may
              be unavailable.
            </p>
          )}
          {!canShow && <p>Symbol absent in this parsed revision.</p>}
          {preview.length > 0 && (
            <pre tabIndex={0} aria-label={`${label} code, scroll to read`}>
              {preview.map((line, index) => (
                <span
                  className="source-line"
                  data-line={line.number}
                  key={line.number}
                >
                  <span className="line-number" aria-hidden="true">
                    {line.number}
                  </span>
                  <code>
                    {colored[index].map((token, i) =>
                      token.kind === "plain" ? (
                        token.text
                      ) : (
                        <span className={`syntax-${token.kind}`} key={i}>
                          {token.text}
                        </span>
                      ),
                    )}
                    {line.clipped && (
                      <span className="clipped"> … [line truncated]</span>
                    )}
                    {"\n"}
                  </code>
                </span>
              ))}
            </pre>
          )}
        </>
      )}
      {truncated && (
        <p className="source-warning">
          Preview truncated: at most {MAX_LINES} lines,{" "}
          {MAX_CHARACTERS.toLocaleString()} characters and {MAX_LINE_CHARACTERS}{" "}
          characters per line. Export contains the complete source file.
        </p>
      )}
    </section>
  );
}

export function ChangesView({
  report,
  selected,
  onSelect,
}: {
  report: Report;
  selected: string | null;
  onSelect: (id: string) => void;
}) {
  const change =
    report.changes.find((c) => c.symbol === selected) ?? report.changes[0];
  const file = report.source_files.find((f) => f.path === change?.path);
  const groups = new Map<string, SymbolChange[]>();
  for (const item of report.changes) {
    const group = groups.get(item.path) ?? [];
    group.push(item);
    groups.set(item.path, group);
  }
  return (
    <div className="changes-view">
      <p className="changes-description">
        Semantic changes only. Comments and line movement alone are ignored.
        Modules include module-level statements and nested definitions.
      </p>
      {groups.size === 0 ? (
        <p>No semantic changes in these snapshots.</p>
      ) : (
        <>
          <details className="change-navigation" open>
            <summary>
              Changed files & symbols{" "}
              <span>
                {groups.size} files · {report.changes.length} symbols
              </span>
            </summary>
            <nav className="change-list" aria-label="Changed symbols by file">
              {[...groups].map(([path, items]) => (
                <div key={path} className="change-file">
                  <h3>
                    <Icon name="file" />
                    {path}
                  </h3>
                  {items.map((item) => (
                    <button
                      key={item.symbol}
                      className={`change-row ${change?.symbol === item.symbol ? "selected" : ""}`}
                      aria-pressed={change?.symbol === item.symbol}
                      onClick={() => onSelect(item.symbol)}
                    >
                      <span className={`change-status ${item.status}`}>
                        {item.status}
                      </span>
                      <strong>{item.symbol.split("::")[1]}</strong>
                    </button>
                  ))}
                </div>
              ))}
            </nav>
          </details>
          {change && file && (
            <section className="code-review" aria-label="Selected changed code">
              <h3>
                {change.symbol.split("::")[1]}{" "}
                <span className={`change-status ${change.status}`}>
                  {change.status}
                </span>
              </h3>
              <p>{file.path} · Exact analyzed snapshots</p>
              <div className="source-columns">
                <SourcePane
                  label="Before"
                  source={file.before}
                  range={change.before}
                />
                <SourcePane
                  label="After"
                  source={file.after}
                  range={change.after}
                />
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
}
