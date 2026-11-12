import type { CSSProperties } from "react";

const paths = {
  branch: "M6 3v12a3 3 0 0 0 6 0V9a3 3 0 0 1 3-3h3M3 6h6m6-3 3 3-3 3",
  tests: "m4 6 2 2 4-4m3 2h7M4 13l2 2 4-4m3 2h7M4 20l2 2 4-4m3 2h7",
  map: "M5 5h5v5H5zM14 14h5v5h-5zM5 14h5v5H5zM8 10v4m2-7h6v7",
  code: "m8 7-5 5 5 5m8-10 5 5-5 5m-3-13-2 16",
  plus: "M12 5v14M5 12h14",
  arrow: "M5 12h14m-5-5 5 5-5 5",
  back: "M19 12H5m5-5-5 5 5 5",
  download: "M12 3v12m-5-5 5 5 5-5M5 16v4h14v-4",
  upload: "M12 16V4m-5 5 5-5 5 5M5 16v4h14v-4",
  close: "m6 6 12 12M6 18 18 6",
  file: "M14 3H5v18h14V8l-5-5v5h5M8 13h8m-8 4h6",
  evidence: "M9 4H4v16h16V4h-5M9 3h6v4H9zM8 12h8m-8 4h5",
  external: "M14 3h7v7m0-7L11 13M10 5H4v15h15v-6",
  clock: "M12 8v5l3 2M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0",
  shield: "m12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6l8-3m-4 9 3 3 5-6",
} as const;
export function Icon({
  name,
  style,
}: {
  name: keyof typeof paths;
  style?: CSSProperties;
}) {
  return (
    <svg
      className="icon"
      style={style}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d={paths[name]} />
    </svg>
  );
}
