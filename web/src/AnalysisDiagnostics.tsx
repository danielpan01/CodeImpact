import { useId, useMemo, useRef, useState } from "react";
import type { Report } from "./types";
import { Icon } from "./Icon";
import {
  classifyNotes,
  defaultNoteFilters,
  groupNotes,
  noteCategories,
  type NoteFileGroup,
  type NoteFilters,
} from "./diagnostics";

const pageSize = 50;
const countLabel = (matching: number, total: number) =>
  matching === total
    ? `${total} ${total === 1 ? "note" : "notes"}`
    : `${matching} of ${total} ${total === 1 ? "note" : "notes"}`;

function NoteEntries({
  group,
  page,
  setPage,
}: {
  group: NoteFileGroup;
  page: number;
  setPage: (page: number) => void;
}) {
  const start = page * pageSize;
  const entries = group.notes.slice(start, start + pageSize);
  const list = useRef<HTMLOListElement>(null);
  const move = (next: number) => {
    setPage(next);
    // Put keyboard users at the new entries; the old next button may be disabled.
    list.current?.focus({ preventScroll: true });
    list.current?.scrollIntoView({ block: "start" });
  };
  return (
    <>
      <ol
        className="diagnostic-entries"
        ref={list}
        tabIndex={-1}
        aria-label="Original analysis notes"
      >
        {entries.map((note) => (
          <li
            className="diagnostic-entry"
            key={note.id}
            data-note-index={note.id}
          >
            <span className="note-number">
              <span className="visually-hidden">Original note </span>
              <span aria-hidden="true">#</span>
              {note.id + 1}
            </span>
            <div>
              <p className="diagnostic-text">{note.text}</p>
              {!note.text && <em>Empty note</em>}
            </div>
          </li>
        ))}
      </ol>
      {group.notes.length > pageSize && (
        <div className="note-pagination">
          <span role="status">
            Showing {start + 1}–{start + entries.length} of {group.notes.length}{" "}
            matching notes in this group
          </span>
          <div>
            <button
              className="secondary"
              disabled={page === 0}
              onClick={() => move(page - 1)}
            >
              Previous notes
            </button>
            <button
              className="secondary"
              disabled={start + pageSize >= group.notes.length}
              onClick={() => move(page + 1)}
            >
              Next notes
            </button>
          </div>
        </div>
      )}
    </>
  );
}

export function AnalysisDiagnostics({ report }: { report: Report }) {
  const id = useId();
  const notes = useMemo(() => classifyNotes(report), [report]);
  const [filters, setFilters] = useState(defaultNoteFilters);
  const [expanded, setExpanded] = useState<Set<string>>(() => new Set());
  const [pages, setPages] = useState<Record<string, number>>({});
  const groups = useMemo(() => groupNotes(notes, filters), [notes, filters]);
  const allGroups = useMemo(
    () => groupNotes(notes, defaultNoteFilters),
    [notes],
  );
  const fileOptions = useMemo(() => {
    const counts = new Map<string | null, number>();
    notes.forEach((n) => counts.set(n.file, (counts.get(n.file) ?? 0) + 1));
    return [...counts].sort(([a], [b]) =>
      a === b ? 0 : a === null ? -1 : b === null ? 1 : a < b ? -1 : 1,
    );
  }, [notes]);
  const update = (next: NoteFilters) => {
    setFilters(next);
    setPages({});
  };
  const toggle = (key: string) =>
    setExpanded((previous) => {
      const next = new Set(previous);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  const matching = groups.reduce((sum, g) => sum + g.matching, 0);
  const filtered =
    !!filters.query || filters.category !== "all" || filters.file !== undefined;
  return (
    <details className="limitations diagnostics">
      <summary>
        <strong>Analysis scope &amp; limitations</strong>
        <span>
          {notes.length} total {notes.length === 1 ? "note" : "notes"}
        </span>
      </summary>
      <div className="diagnostics-body">
        <p className="diagnostics-caution">
          <Icon name="info" />{" "}
          <span>
            Static Python analysis is incomplete. A missing dependency path does
            not establish safety. Keep the full test suite as a gate.
          </span>
        </p>
        {notes.length === 0 ? (
          <div className="diagnostic-empty">
            <h3>No analysis notes</h3>
            <p>
              This report contains no notes. This does not establish safety.
            </p>
          </div>
        ) : (
          <>
            <div
              className="diagnostic-toolbar"
              role="search"
              aria-label="Filter analysis notes"
            >
              <label className="note-search">
                Search analysis notes
                <input
                  type="search"
                  placeholder="Find text in any note…"
                  value={filters.query}
                  onChange={(e) =>
                    update({ ...filters, query: e.target.value })
                  }
                />
              </label>
              {allGroups.length > 1 && (
                <label>
                  Note category
                  <select
                    aria-label="Note category"
                    value={filters.category}
                    onChange={(e) =>
                      update({
                        ...filters,
                        category: e.target.value as NoteFilters["category"],
                      })
                    }
                  >
                    <option value="all">All categories ({notes.length})</option>
                    {allGroups.map((g) => (
                      <option key={g.category} value={g.category}>
                        {noteCategories[g.category]} ({g.total})
                      </option>
                    ))}
                  </select>
                </label>
              )}
              {fileOptions.length > 1 && (
                <label>
                  Note file
                  <select
                    aria-label="Note file"
                    value={
                      filters.file === undefined
                        ? "all"
                        : JSON.stringify(filters.file)
                    }
                    onChange={(e) =>
                      update({
                        ...filters,
                        file:
                          e.target.value === "all"
                            ? undefined
                            : (JSON.parse(e.target.value) as string | null),
                      })
                    }
                  >
                    <option value="all">All files / report-wide</option>
                    {fileOptions.map(([file, count]) => (
                      <option
                        key={JSON.stringify(file)}
                        value={JSON.stringify(file)}
                      >
                        {file ?? "No confirmed file / report-wide"} ({count})
                      </option>
                    ))}
                  </select>
                </label>
              )}
            </div>
            <div className="diagnostic-results">
              <span role="status" aria-label="Note results" aria-live="polite">
                {matching} matching {matching === 1 ? "note" : "notes"} of{" "}
                {notes.length} total
              </span>
              <button
                className="text-button"
                disabled={!filtered}
                onClick={() => update(defaultNoteFilters)}
              >
                Reset notes
              </button>
            </div>
            <p className="diagnostic-help">
              Groups show matching / total occurrences. Search includes complete
              text in every group and page. Filtering changes only this view;
              exports keep every original note.
            </p>
            {groups.length === 0 ? (
              <div className="diagnostic-empty">
                <Icon name="search" />
                <h3>No matching notes</h3>
                <p>
                  Try different text or reset the note filters. All{" "}
                  {notes.length} original notes remain in the report.
                </p>
              </div>
            ) : (
              <div className="diagnostic-groups">
                {groups.map((g, gi) => {
                  const open = expanded.has(g.category);
                  return (
                    <section className="diagnostic-category" key={g.category}>
                      <h3>
                        <button
                          className="diagnostic-disclosure"
                          aria-expanded={open}
                          aria-controls={`${id}-category-${gi}`}
                          onClick={() => toggle(g.category)}
                        >
                          <Icon name="chevron" />
                          <span>{noteCategories[g.category]}</span>
                          <small>{countLabel(g.matching, g.total)}</small>
                        </button>
                      </h3>
                      <div id={`${id}-category-${gi}`} hidden={!open}>
                        {open &&
                          g.files.map((file, fi) => {
                            const fileOpen =
                              file.file === null || expanded.has(file.id);
                            return (
                              <div className="diagnostic-file" key={file.id}>
                                {file.file === null ? (
                                  <p className="diagnostic-file-label">
                                    {g.category === "scope"
                                      ? "Report-wide"
                                      : "No confirmed file"}
                                  </p>
                                ) : (
                                  <h4>
                                    <button
                                      className="diagnostic-disclosure"
                                      aria-expanded={fileOpen}
                                      aria-controls={`${id}-file-${gi}-${fi}`}
                                      onClick={() => toggle(file.id)}
                                    >
                                      <Icon name="chevron" />
                                      <code>{file.file}</code>
                                      <small>
                                        {countLabel(
                                          file.notes.length,
                                          file.total,
                                        )}
                                      </small>
                                    </button>
                                  </h4>
                                )}
                                <div
                                  id={`${id}-file-${gi}-${fi}`}
                                  hidden={!fileOpen}
                                >
                                  {fileOpen && (
                                    <NoteEntries
                                      group={file}
                                      page={pages[file.id] ?? 0}
                                      setPage={(page) =>
                                        setPages((previous) => ({
                                          ...previous,
                                          [file.id]: page,
                                        }))
                                      }
                                    />
                                  )}
                                </div>
                              </div>
                            );
                          })}
                      </div>
                    </section>
                  );
                })}
              </div>
            )}
            <p className="diagnostic-footnote">
              Note numbers follow the original report order. Repeated messages
              count separately. General / unclassified keeps formats and file
              references we cannot confirm.
            </p>
          </>
        )}
      </div>
    </details>
  );
}
