// Display-only lexical coloring. Input is the bounded preview, never executable HTML.
// This is deliberately not a parser; malformed Python remains visible verbatim.
export type SourceToken = {
  text: string;
  kind: "plain" | "keyword" | "string" | "comment" | "number";
};
const keywords = new Set(
  "False None True and as assert async await break case class continue def del elif else except finally for from global if import in is lambda match nonlocal not or pass raise return try while with yield".split(
    " ",
  ),
);
export function colorSource(lines: string[]): SourceToken[][] {
  let triple = "";
  return lines.map((line) => {
    const tokens: SourceToken[] = [];
    const add = (text: string, kind: SourceToken["kind"]) => {
      const last = tokens.at(-1);
      if (last?.kind === kind) last.text += text;
      else tokens.push({ text, kind });
    };
    let i = 0;
    while (i < line.length) {
      const start = i;
      if (triple) {
        while (i < line.length) {
          if (line[i] === "\\") {
            i = Math.min(i + 2, line.length);
            continue;
          }
          if (line.startsWith(triple, i)) {
            i += 3;
            triple = "";
            break;
          }
          i++;
        }
        add(line.slice(start, i), "string");
      } else if (line[i] === "#") {
        add(line.slice(i), "comment");
        break;
      } else if (line[i] === "'" || line[i] === '"') {
        const quote = line[i];
        if (line.startsWith(quote.repeat(3), i)) {
          triple = quote.repeat(3);
          add(triple, "string");
          i += 3;
        } else {
          i++;
          while (i < line.length) {
            if (line[i] === "\\") {
              i = Math.min(i + 2, line.length);
              continue;
            }
            if (line[i++] === quote) break;
          }
          add(line.slice(start, i), "string");
        }
      } else if (/[A-Za-z_]/.test(line[i])) {
        while (i < line.length && /[A-Za-z_0-9]/.test(line[i])) i++;
        const word = line.slice(start, i);
        add(word, keywords.has(word) ? "keyword" : "plain");
      } else if (/[0-9]/.test(line[i])) {
        const number = line
          .slice(i)
          .match(
            /^(?:0[xX][\da-fA-F_]+|0[bB][01_]+|0[oO][0-7_]+|\d[\d_]*(?:\.[\d_]*)?(?:[eE][+-]?[\d_]+)?)[jJ]?/,
          )![0];
        i += number.length;
        add(number, "number");
      } else {
        add(line[i++], "plain");
      }
    }
    return tokens;
  });
}
