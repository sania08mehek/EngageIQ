import RiskBadge from './RiskBadge';
import type { RiskMix } from '../api/types';
import type { RiskCategory } from '../lib/pace';

const ORDER: RiskCategory[] = ['healthy', 'moderate', 'at-risk'];

interface Props {
  mix: RiskMix;
  legend?: boolean;
}

export default function RiskBar({ mix, legend = false }: Props) {
  const label = ORDER.map((k) => `${mix[k]} ${k}`).join(', ');
  return (
    <div className="riskbar-wrap">
      <div className="riskbar" role="img" aria-label={label}>
        {ORDER.map((k) => (mix[k] > 0 ? <span key={k} className={`riskbar-seg seg-${k}`} style={{ flexGrow: mix[k] }} /> : null))}
      </div>
      {legend && (
        <ul className="riskbar-legend">
          {ORDER.map((k) => (
            <li key={k}>
              <RiskBadge category={k} />
              <strong>{mix[k]}</strong>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
