export default function Button({ children, loading }) {
  return (
    <button className="btn-primary" disabled={loading} type="submit">
      {loading ? 'Loading...' : children}
    </button>
  );
}