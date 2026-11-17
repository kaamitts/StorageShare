import { useState, useRef, useEffect } from 'react';
import { useLang } from '../lib/lang-context';

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

function pad(value) {
  return String(value).padStart(2, '0');
}

function digitsOnly(value) {
  return value.replace(/\D/g, '').slice(0, 2);
}

export default function DateTimeField({
  label, date, time, onDate, onTime, min, slots, error, dateAria, timeAria,
}) {
  const { lang, t } = useLang();
  const locale = LOCALES[lang] || 'en-GB';
  const [open, setOpen] = useState('');
  const [month, setMonth] = useState(() => startOfMonth(new Date()));
  const [hours, setHours] = useState('');
  const [minutes, setMinutes] = useState('');
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

  function toggleTime() {
    if (open !== 'time') {
      const [currentHours = '', currentMinutes = ''] = (time || '').split(':');
      setHours(currentHours);
      setMinutes(currentMinutes);
    }
    setOpen(open === 'time' ? '' : 'time');
  }

  function editTime(nextHours, nextMinutes) {
    setHours(nextHours);
    setMinutes(nextMinutes);
    if (nextHours === '' || nextMinutes === '') return;
    const h = Number(nextHours);
    const m = Number(nextMinutes);
    if (h <= 23 && m <= 59) onTime(`${pad(h)}:${pad(m)}`);
  }

  function normalizeTime() {
    if (hours === '' || minutes === '') return;
    const h = Math.min(23, Number(hours));
    const m = Math.min(59, Number(minutes));
    setHours(pad(h));
    setMinutes(pad(m));
    onTime(`${pad(h)}:${pad(m)}`);
  }

  function pickSlot(slot) {
    const [slotHours, slotMinutes] = slot.split(':');
    setHours(slotHours);
    setMinutes(slotMinutes);
    onTime(slot);
    setOpen('');
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
      <button type="button" aria-label={timeAria} aria-expanded={open === 'time'}
        className={`picker-control${error ? ' error' : ''}${time ? '' : ' empty'}`}
        onClick={toggleTime}>{time || t.timeLabel}</button>
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

    {open === 'time' && <div className="picker-pop picker-times">
      <div className="picker-time-entry">
        <input type="text" inputMode="numeric" maxLength={2} value={hours}
          aria-label={t.hoursLabel} placeholder="00" onBlur={normalizeTime}
          onChange={event => editTime(digitsOnly(event.target.value), minutes)} />
        <span className="picker-colon">:</span>
        <input type="text" inputMode="numeric" maxLength={2} value={minutes}
          aria-label={t.minutesLabel} placeholder="00" onBlur={normalizeTime}
          onChange={event => editTime(hours, digitsOnly(event.target.value))} />
      </div>
      <span className="picker-quick">{t.quickPick}</span>
      <div className="picker-slots">
        {slots.map(slot => <button type="button" key={slot}
          className={`picker-slot${slot === time ? ' selected' : ''}`}
          onClick={() => pickSlot(slot)}>{slot}</button>)}
      </div>
    </div>}

    {error && <span className="err-msg">{error}</span>}
  </div>;
}