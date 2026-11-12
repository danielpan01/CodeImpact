import { useRef, type RefObject } from "react";
import { Icon } from "./Icon";

export function AnalysisInput({
  busy,
  prUrl,
  setPrUrl,
  onPR,
  onDemo,
  onUpload,
  onClose,
  inputRef,
}: {
  busy: boolean;
  prUrl: string;
  setPrUrl: (url: string) => void;
  onPR: () => void;
  onDemo: () => void;
  onUpload: (file: File) => void;
  onClose?: () => void;
  inputRef: RefObject<HTMLInputElement | null>;
}) {
  const fileInput = useRef<HTMLInputElement>(null);
  return (
    <section className="analysis-input" aria-label="New analysis">
      <div className="input-heading">
        <div>
          <span className="eyebrow">Python change analysis</span>
          <h1>Start with a change.</h1>
          <p>
            Find the tests that deserve attention, then follow the evidence.
          </p>
        </div>
        {onClose && (
          <button
            className="icon-button"
            aria-label="Close analysis input"
            onClick={onClose}
            disabled={busy}
          >
            <Icon name="close" />
          </button>
        )}
      </div>
      <form
        className="pr-form"
        aria-label="Analyze a public GitHub pull request"
        onSubmit={(event) => {
          event.preventDefault();
          onPR();
        }}
      >
        <label htmlFor="pr-url">Analyze a GitHub pull request</label>
        <p id="pr-help">
          Public GitHub PRs with Python source. Read as data; never executed.
        </p>
        <div className="pr-input-row">
          <input
            id="pr-url"
            ref={inputRef}
            type="url"
            required
            maxLength={300}
            placeholder="https://github.com/owner/repo/pull/123"
            aria-describedby="pr-help"
            value={prUrl}
            onChange={(event) => setPrUrl(event.target.value)}
            disabled={busy}
            spellCheck={false}
          />
          <button className="primary" type="submit" disabled={busy}>
            Analyze PR <Icon name="arrow" />
          </button>
        </div>
      </form>
      <div className="input-alternatives">
        <div>
          <Icon name="upload" />
          <div>
            <strong>Have a snapshot pair?</strong>
            <p>Upload before / after Python files as JSON.</p>
          </div>
          <button
            className="secondary"
            disabled={busy}
            onClick={() => fileInput.current?.click()}
          >
            Analyze snapshots
          </button>
          <input
            className="visually-hidden"
            ref={fileInput}
            aria-label="Upload snapshot JSON"
            type="file"
            accept=".json,application/json"
            disabled={busy}
            tabIndex={-1}
            onChange={(event) => {
              const file = event.target.files?.[0];
              if (file) onUpload(file);
              event.target.value = "";
            }}
          />
        </div>
        <div>
          <Icon name="branch" />
          <div>
            <strong>Explore the checkout demo</strong>
            <p>A discount change, three tests, traceable paths.</p>
          </div>
          <button className="secondary" disabled={busy} onClick={onDemo}>
            Load demo
          </button>
        </div>
      </div>
      <p className="input-footnote">
        <Icon name="shield" /> Static evidence guides review. Keep the full test
        suite as your merge gate.
      </p>
    </section>
  );
}
