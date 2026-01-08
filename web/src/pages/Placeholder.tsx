import { AppShell } from '../components/AppShell'

type PlaceholderProps = {
  title: string
  eyebrow?: string
  subtitle?: string
}

export function Placeholder({ title, eyebrow, subtitle }: PlaceholderProps) {
  return (
    <AppShell
      title={title}
      eyebrow={eyebrow}
      subtitle={subtitle ?? 'This view is queued for implementation.'}
    >
      <section className="panel panel--wide">
        <h2>In progress</h2>
        <p className="panel__meta">
          This route is scaffolded for navigation. Connect data sources next.
        </p>
      </section>
    </AppShell>
  )
}
