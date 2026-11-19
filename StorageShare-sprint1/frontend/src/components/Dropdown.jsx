import { useState, useRef, useEffect } from 'react';

export default function Dropdown({ value, options, onChange, placeholder, ariaLabel, error, wide }) {
  const [open, setOpen] = useState(false);
  const root = useRef(null);

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

  const current = options.find(option => option.value === value);

  return <div className={`dropdown${wide ? '' : ' dropdown-narrow'}`} ref={root}>
    <button type="button" aria-label={ariaLabel} aria-expanded={open} aria-haspopup="listbox"
      className={`dropdown-control${error ? ' error' : ''}${current ? '' : ' empty'}`}
      onClick={() => setOpen(!open)}>
      <span className="dropdown-value">{current ? current.label : placeholder}</span>
      <span className="dropdown-caret" aria-hidden="true" />
    </button>
    {open && <div className="dropdown-pop" role="listbox">
      {options.map(option => <button type="button" key={option.value} role="option"
        aria-selected={option.value === value}
        className={`dropdown-option${option.value === value ? ' selected' : ''}`}
        onClick={() => { onChange(option.value); setOpen(false); }}>{option.label}</button>)}
    </div>}
  </div>;
}