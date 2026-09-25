import { Link } from 'react-router-dom';

export default function NotFound() {
  return (
    <div className="wrap page">
      <div className="notice">
        <h1>This page does not exist</h1>
        <p>Check the address, or go back to somewhere that does.</p>
        <div className="actions">
          <Link className="btn" to="/dashboard">Open the dashboard</Link>
          <Link className="btn btn-ghost" to="/">Go to the overview</Link>
        </div>
      </div>
    </div>
  );
}
