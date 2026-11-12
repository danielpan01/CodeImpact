import { useEffect, useLayoutEffect, useState } from "react";

export type Theme = "light" | "dark";
const preferenceKey = "codeimpact.theme";
function savedTheme(): Theme | null {
  try {
    const value = localStorage.getItem(preferenceKey);
    return value === "light" || value === "dark" ? value : null;
  } catch {
    return null;
  }
}
const systemTheme = (): Theme =>
  window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";

export function useTheme() {
  const [theme, setTheme] = useState<Theme>(
    () => savedTheme() ?? systemTheme(),
  );
  // Storage is optional: private/restricted browser contexts still get both themes.
  const [explicit, setExplicit] = useState(() => savedTheme() !== null);
  useLayoutEffect(() => {
    document.documentElement.dataset.theme = theme;
    document.documentElement.style.colorScheme = theme;
    document
      .querySelector('meta[name="theme-color"]')
      ?.setAttribute("content", theme === "dark" ? "#111722" : "#172236");
  }, [theme]);
  useEffect(() => {
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const followSystem = () => {
      if (!explicit) setTheme(systemTheme());
    };
    const sync = (event: StorageEvent) => {
      if (event.key !== preferenceKey && event.key !== null) return;
      const stored = savedTheme();
      setExplicit(stored !== null);
      setTheme(stored ?? systemTheme());
    };
    media.addEventListener("change", followSystem);
    window.addEventListener("storage", sync);
    return () => {
      media.removeEventListener("change", followSystem);
      window.removeEventListener("storage", sync);
    };
  }, [explicit]);
  return {
    theme,
    toggleTheme: () => {
      const next = theme === "light" ? "dark" : "light";
      setTheme(next);
      setExplicit(true);
      try {
        localStorage.setItem(preferenceKey, next);
      } catch {
        /* In-memory choice still works. */
      }
    },
  };
}
