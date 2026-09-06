interface Props {
  title: string;
  description?: string;
}

export default function PlaceholderPage({ title, description }: Props) {
  return (
    <div>
      <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: '#111827', margin: '0 0 0.5rem' }}>
        {title}
      </h1>
      <p style={{ color: '#6b7280', margin: 0 }}>
        {description ?? 'Coming soon.'}
      </p>
    </div>
  );
}
