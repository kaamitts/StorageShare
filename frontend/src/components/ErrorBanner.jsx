export default function ErrorBanner({ message }) {
  if (!message) return null;
  return <div className="banner">{message}</div>;
}