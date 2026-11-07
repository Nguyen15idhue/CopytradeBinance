import { useTheme, type ThemeMode } from "../lib/theme";

const OPTIONS: Array<{ value: ThemeMode; label: string; icon: string }> = [
  { value: "light", label: "Sáng", icon: "☀" },
  { value: "dark", label: "Tối", icon: "☾" },
  { value: "system", label: "Hệ thống", icon: "⌥" },
];

export default function ThemeToggle() {
  const { mode, setMode } = useTheme();
  return (
    <div
      role="group"
      aria-label="Chế độ giao diện"
      className="flex items-center rounded-lg border border-line bg-panel p-0.5"
    >
      {OPTIONS.map((option) => (
        <button
          key={option.value}
          type="button"
          aria-pressed={mode === option.value}
          title={`Chế độ ${option.label.toLowerCase()}`}
          onClick={() => setMode(option.value)}
          className={`rounded-md px-2 py-1 text-xs transition ${
            mode === option.value
              ? "bg-elevated text-strong"
              : "text-muted hover:text-body"
          }`}
        >
          <span aria-hidden="true">{option.icon}</span>
          <span className="ml-1 hidden sm:inline">{option.label}</span>
        </button>
      ))}
    </div>
  );
}
