export default function LoadingSpinner({ text = 'Loading...' }) {
  return (
    <div className="loading-screen">
      <div className="spinner" />
      <p>{text}</p>
    </div>
  );
}
