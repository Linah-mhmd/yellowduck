export default function PageHeader({ eyebrow, title, subtitle, children }) {
  return (
    <div className="page-header animate-fade-up">
      {eyebrow && <span className="eyebrow">{eyebrow}</span>}
      <h1>{title}</h1>
      {subtitle && <p>{subtitle}</p>}
      {children}
    </div>
  );
}
