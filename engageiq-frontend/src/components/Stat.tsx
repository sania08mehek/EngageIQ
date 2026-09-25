import type { ReactNode } from 'react';
import { signed } from '../lib/format';

interface Props {
  label: string;
  value: string;
  delta?: number;
  /** Shown instead of a delta */
  note?: ReactNode;
  tone?: 'ink' | 'ehs' | 'opi';
}

export default function Stat({ label, value, delta, note, tone = 'ink' }: Props) {
  const dir = delta === undefined ? 'flat' : delta > 0.005 ? 'up' : delta < -0.005 ? 'down' : 'flat';
  return (
    <div className={`stat stat-${tone}`}>
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
      {delta !== undefined && (
        <div className={`stat-delta delta-${dir}`}>
          {signed(delta)} <span>vs 4 weeks ago</span>
        </div>
      )}
      {note && <div className="stat-note">{note}</div>}
    </div>
  );
}
