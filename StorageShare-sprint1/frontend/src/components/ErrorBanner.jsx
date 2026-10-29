export default function ErrorBanner({ message }) {
  if (!message) return null;
  return <div className="banner" role="alert">{message}</div>;
}