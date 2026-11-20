export default function Button({ children, loading, disabled = false }) {
  return (
    <button className="btn-primary" disabled={loading || disabled} type="submit">
      {loading ? 'Loading...' : children}
    </button>
  );
}
