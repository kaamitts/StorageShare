import { useEffect, useRef, useState } from 'react';

function digitsOnly(value) {
  return value.replace(/\D/g, '').slice(0, 2);
}

function pad(value) {
  return String(value).padStart(2, '0');
}

export default function TimePicker({
  time, onTime, slots, ariaLabel, emptyLabel, hoursLabel, minutesLabel, error,
  quickPickLabel, onOpen, disabled = false,
}) {
  const [open, setOpen] = useState(false);
  const [hours, setHours] = useState('');
  const [minutes, setMinutes] = useState('');
  const root = useRef(null);

  useEffect(() => {
    if (disabled) setOpen(false);
  }, [disabled]);

  useEffect(() => {
    if (!open) return undefined;
    function onDown(event) {
      if (root.current && !root.current.contains(event.target)) setOpen(false);
    }
    function onKey(event) { if (event.key === 'Escape') setOpen(false); }
    document.addEventListener('mousedown', onDown);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('mousedown', onDown);
      document.removeEventListener('keydown', onKey);
    };
  }, [open]);

  function toggle() {
    if (!open) {
      const [currentHours = '', currentMinutes = ''] = (time || '').split(':');
      setHours(currentHours);
      setMinutes(currentMinutes);
      onOpen?.();
    }
    setOpen(value => !value);
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
    setOpen(false);
  }

  return <div className="time-picker" ref={root}>
    <button type="button" aria-label={ariaLabel} aria-expanded={open} disabled={disabled}
      className={`picker-control${error ? ' error' : ''}${time ? '' : ' empty'}`}
      onClick={toggle}>{time || emptyLabel}</button>
    {open && <div className="picker-pop picker-times">
      <div className="picker-time-entry">
        <input type="text" inputMode="numeric" maxLength={2} value={hours}
          aria-label={hoursLabel} placeholder="00" onBlur={normalizeTime}
          onChange={event => editTime(digitsOnly(event.target.value), minutes)} />
        <span className="picker-colon">:</span>
        <input type="text" inputMode="numeric" maxLength={2} value={minutes}
          aria-label={minutesLabel} placeholder="00" onBlur={normalizeTime}
          onChange={event => editTime(hours, digitsOnly(event.target.value))} />
      </div>
      {quickPickLabel && <span className="picker-quick">{quickPickLabel}</span>}
      <div className="picker-slots">
        {slots.map(slot => <button type="button" key={slot}
          className={`picker-slot${slot === time ? ' selected' : ''}`}
          onClick={() => pickSlot(slot)}>{slot}</button>)}
      </div>
    </div>}
  </div>;
}
