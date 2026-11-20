import { useLang } from '../lib/lang-context';
import { useTheme } from '../lib/ThemeContext';

export default function ThemeToggle({ className = 'header-theme-button' }) {
  const { t } = useLang();
  const { theme, toggleTheme } = useTheme();

  return <button className={className} type="button" onClick={toggleTheme}
    aria-label={theme === 'dark' ? t.lightTheme : t.darkTheme}
    title={theme === 'dark' ? t.lightTheme : t.darkTheme}
    aria-pressed={theme === 'dark'}>
    <span aria-hidden="true">{theme === 'dark' ? '☀' : '☾'}</span>
  </button>;
}
