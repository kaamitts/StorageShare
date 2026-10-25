export default function Field({ label, type = 'text', value, onChange, error, placeholder }) {
  return (
    <div className="field">
      <label>{label}</label>
      <input
        className={error ? 'error' : ''}
        type={type}
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
      />
      {error && <span className="err-msg">! {error}</span>}
    </div>
  );
}