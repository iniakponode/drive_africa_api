import { Link } from 'react-router-dom'
import { AppShell } from '../components/AppShell'

export function AdminLanding() {
  return (
    <AppShell
      title="Admin Command Center"
      eyebrow="Role switch"
      subtitle="Manage core configuration or jump into role dashboards."
      actions={<div className="pill pill--active">Admin</div>}
    >
      <section className="kpi-grid">
        <div className="card">
          <p className="card__label">API Clients</p>
          <p className="card__detail">Create keys and manage scopes.</p>
          <Link className="ghost ghost--light" to="/admin/api-clients">
            Manage API clients
          </Link>
        </div>
        <div className="card">
          <p className="card__label">Dataset Access</p>
          <p className="card__detail">Control role-based dataset access.</p>
          <Link className="ghost ghost--light" to="/admin/dataset-access">
            Edit dataset policy
          </Link>
        </div>
        <div className="card">
          <p className="card__label">Cloud Endpoints</p>
          <p className="card__detail">Update external integration URLs.</p>
          <Link className="ghost ghost--light" to="/admin/cloud-endpoints">
            Configure endpoints
          </Link>
        </div>
        <div className="card">
          <p className="card__label">Insurance Partners</p>
          <p className="card__detail">Create partners and map drivers.</p>
          <Link className="ghost ghost--light" to="/admin/insurance-partners">
            Manage partners
          </Link>
        </div>
        <div className="card">
          <p className="card__label">Driver Profiles</p>
          <p className="card__detail">Create/update driver identities.</p>
          <Link className="ghost ghost--light" to="/admin/driver-profiles">
            Manage profiles
          </Link>
        </div>
      </section>

      <section className="kpi-grid">
        <div className="card">
          <p className="card__label">Fleet Manager View</p>
          <p className="card__detail">
            Monitor safety KPIs and bad-day performance.
          </p>
          <Link className="ghost ghost--light" to="/fleet">
            Open fleet dashboard
          </Link>
        </div>
        <div className="card">
          <p className="card__label">Driver View</p>
          <p className="card__detail">
            Inspect personal performance and leaderboards.
          </p>
          <Link className="ghost ghost--light" to="/driver">
            Open driver dashboard
          </Link>
        </div>
        <div className="card">
          <p className="card__label">Researcher View</p>
          <p className="card__detail">
            Explore summaries and export datasets.
          </p>
          <Link className="ghost ghost--light" to="/researcher">
            Open researcher dashboard
          </Link>
        </div>
        <div className="card">
          <p className="card__label">Insurance View</p>
          <p className="card__detail">
            Audit telematics performance and alerts.
          </p>
          <Link className="ghost ghost--light" to="/insurance">
            Open insurance dashboard
          </Link>
        </div>
      </section>
    </AppShell>
  )
}
