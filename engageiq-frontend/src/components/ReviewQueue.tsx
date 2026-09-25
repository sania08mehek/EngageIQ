import { Link } from 'react-router-dom';
import RiskBadge from './RiskBadge';
import { outcomeLabel, type QueueItem } from '../api/types';

export default function ReviewQueue({ items }: { items: QueueItem[] }) {
  if (!items.length) {
    return <p className="muted">No patterns need a look right now.</p>;
  }
  return (
    <ul className="queue">
      {items.map((q) => (
        <li key={q.employee.id}>
          <Link to={`/dashboard/people/${q.employee.id}`}>
            <span className="queue-top">
              <strong>{q.employee.name}</strong>
              <RiskBadge category={q.category} />
            </span>
            <span className="queue-meta">{q.employee.roleName} on {q.employee.teamName}</span>
            <span className="queue-headline">{q.headline}</span>
            <span className={`status status-${q.status}`}>
              {q.status === 'reviewed' && q.lastOutcome ? `Reviewed: ${outcomeLabel(q.lastOutcome)}` : 'Needs review'}
            </span>
          </Link>
        </li>
      ))}
    </ul>
  );
}
