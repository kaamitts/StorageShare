import { useState, useRef, useEffect } from 'react';
import { useLang } from '../lib/lang-context';
import TimePicker from './TimePicker';

const LOCALES = { kk: 'kk-KZ', ru: 'ru-RU', en: 'en-GB' };

function toISODate(day) {
  return day.toLocaleDateString('en-CA');
}

function startOfMonth(day) {
  return new Date(day.getFullYear(), day.getMonth(), 1);
}

function monthGrid(month) {
  const first = startOfMonth(month);
  const offset = (first.getDay() + 6) % 7;
  const start = new Date(first);
  start.setDate(first.getDate() - offset);
  return Array.from({ length: 42 }, (unused, index) => {
    const day = new Date(start);
    day.setDate(start.getDate() + index);
    return day;
  });
}

export default function DateTimeField({
  label, date, time, onDate, onTime, min, slots, error, dateAria, timeAria,
}) {
  const { lang, t } = useLang();
  const locale = LOCALES[lang] || 'en-GB';
  const [open, setOpen] = useState('');
  const [month, setMonth] = useState(() => startOfMonth(new Date()));
  const root = useRef(null);

  useEffect(() => {
    if (!open) return undefined;
    function onDown(event) {
      if (root.current && !root.current.contains(event.target)) setOpen('');
    }
    function onKey(event) { if (event.key === 'Escape') setOpen(''); }
    document.addEventListener('mousedown', onDown);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('mousedown', onDown);
      document.removeEventListener('keydown', onKey);
    };
  }, [open]);

  function toggleDate() {
    if (open !== 'date' && date) setMonth(startOfMonth(new Date(`${date}T00:00`)));
    setOpen(open === 'date' ? '' : 'date');
  }

  const days = monthGrid(month);
  const weekdays = days.slice(0, 7).map(day => day.toLocaleDateString(locale, { weekday: 'short' }));
  const shownDate = date
    ? new Date(`${date}T00:00`).toLocaleDateString(locale, { day: '2-digit', month: '2-digit', year: 'numeric' })
    : t.dateLabel;

  return <div className="field picker-field" ref={root}>
    <label>{label}</label>
    <div className="field-split">
      <button type="button" aria-label={dateAria} aria-expanded={open === 'date'}
        className={`picker-control${error ? ' error' : ''}${date ? '' : ' empty'}`}
        onClick={toggleDate}>{shownDate}</button>
      <TimePicker time={time} onTime={onTime} slots={slots} ariaLabel={timeAria}
        emptyLabel={t.chooseTime} hoursLabel={t.hoursLabel} minutesLabel={t.minutesLabel}
        quickPickLabel={t.quickPick} error={error} onOpen={() => setOpen('')} />
    </div>

    {open === 'date' && <div className="picker-pop">
      <div className="picker-head">
        <button type="button" className="picker-nav" aria-label={t.prevMonth}
          onClick={() => setMonth(m => new Date(m.getFullYear(), m.getMonth() - 1, 1))}>‹</button>
        <span className="picker-month">
          {month.toLocaleDateString(locale, { month: 'long', year: 'numeric' })}
        </span>
        <button type="button" className="picker-nav" aria-label={t.nextMonth}
          onClick={() => setMonth(m => new Date(m.getFullYear(), m.getMonth() + 1, 1))}>›</button>
      </div>
      <div className="picker-grid">
        {weekdays.map(name => <span className="picker-weekday" key={name}>{name}</span>)}
        {days.map(day => {
          const iso = toISODate(day);
          return <button type="button" key={iso} disabled={Boolean(min) && iso < min}
            className={`picker-day${iso === date ? ' selected' : ''}${day.getMonth() === month.getMonth() ? '' : ' outside'}`}
            onClick={() => { onDate(iso); setOpen(''); }}>{day.getDate()}</button>;
        })}
      </div>
    </div>}

    {error && <span className="err-msg">{error}</span>}
  </div>;
}
