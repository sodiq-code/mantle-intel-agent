import { useState, useEffect, useCallback } from "react";
import { Sun, Moon } from "lucide-react";
import { G } from "./Shared.jsx";

const THEME_KEY = "mantle-intel-theme";

// Shared theme hook — sets the data-theme attribute on <html>
export function useTheme() {
  const [theme, setTheme] = useState("dark");

  useEffect(() => {
    const saved = typeof localStorage !== "undefined" && localStorage.getItem(THEME_KEY);
    const initial = saved || "dark";
    setTheme(initial);
    document.documentElement.setAttribute("data-theme", initial);
  }, []);

  const toggle = useCallback(() => {
    setTheme(prev => {
      const next = prev === "dark" ? "light" : "dark";
      try { localStorage.setItem(THEME_KEY, next); } catch {}
      document.documentElement.setAttribute("data-theme", next);
      return next;
    });
  }, []);

  return { theme, toggle };
}

export function ThemeToggle() {
  const { theme, toggle } = useTheme();
  const isDark = theme === "dark";
  return (
    <button onClick={toggle}
      title={`Switch to ${isDark ? "light" : "dark"} mode`}
      aria-label="Toggle theme"
      className="relative p-2 rounded-lg border border-white/10 hover:bg-white/5 text-gray-500 hover:text-white transition-all overflow-hidden group">
      <div className="relative w-3.5 h-3.5">
        <Sun size={14}
          className="absolute inset-0 transition-all duration-300"
          style={{
            opacity: isDark ? 0 : 1,
            transform: isDark ? "rotate(-90deg) scale(0.5)" : "rotate(0deg) scale(1)",
            color: "#EAB308"
          }}/>
        <Moon size={14}
          className="absolute inset-0 transition-all duration-300"
          style={{
            opacity: isDark ? 1 : 0,
            transform: isDark ? "rotate(0deg) scale(1)" : "rotate(90deg) scale(0.5)",
            color: G
          }}/>
      </div>
    </button>
  );
}
