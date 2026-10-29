import { useId } from 'react';
export default function Field({ label, type = 'text', value, onChange, error, placeholder }) {
  const id = useId();
  return <div className="field">
    <label htmlFor={id}>{label}</label>
    <input id={id} className={error ? 'error' : ''} type={type} value={value}
      onChange={e => onChange(e.target.value)} placeholder={placeholder}
      aria-invalid={Boolean(error)} aria-describedby={error ? `${id}-error` : undefined} />
    {error && <span id={`${id}-error`} className="err-msg">{error}</span>}
  </div>;
}
