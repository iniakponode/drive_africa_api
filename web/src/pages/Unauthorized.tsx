import { Link } from 'react-router-dom'

export function Unauthorized() {
  return (
    <div className="page-status">
      <h2>Access denied</h2>
      <p>Your API key does not have access to this view.</p>
      <Link className="ghost ghost--light" to="/">
        Go back
      </Link>
    </div>
  )
}
