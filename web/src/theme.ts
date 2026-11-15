import { useLayoutEffect, useRef, useState } from "react";

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
  const explicit = useRef(false);
  useLayoutEffect(() => {
    document.documentElement.dataset.theme = theme;
    document.documentElement.style.colorScheme = theme;
    document
      .querySelector('meta[name="theme-color"]')
      ?.setAttribute("content", theme === "dark" ? "#111722" : "#172236");
  }, [theme]);
  useLayoutEffect(() => {
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const followSystem = () => {
      if (!explicit.current) setTheme(systemTheme());
    };
    const reconcile = () => {
      const stored = savedTheme();
      explicit.current = stored !== null;
      setTheme(stored ?? systemTheme());
    };
    const sync = (event: StorageEvent) => {
      if (event.key === preferenceKey || event.key === null) reconcile();
    };
    media.addEventListener("change", followSystem);
    window.addEventListener("storage", sync);
    // Another tab may have written after the initial render read the preference.
    // Subscribe first, then reconcile before the controls become interactive.
    reconcile();
    return () => {
      media.removeEventListener("change", followSystem);
      window.removeEventListener("storage", sync);
    };
  }, []);
  return {
    theme,
    toggleTheme: () => {
      const next = theme === "light" ? "dark" : "light";
      setTheme(next);
      explicit.current = true;
      try {
        localStorage.setItem(preferenceKey, next);
      } catch {
        /* In-memory choice still works. */
      }
    },
  };
}
