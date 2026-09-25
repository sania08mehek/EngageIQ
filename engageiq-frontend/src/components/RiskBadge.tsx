import type { ReactElement } from 'react';
import { CATEGORY_LABEL, type RiskCategory } from '../lib/pace';

// Shape as well as color, so the status never depends on color alone.
const GLYPH: Record<RiskCategory, ReactElement> = {
  healthy: <circle cx="6" cy="6" r="4.5" />,
  moderate: <rect x="2" y="2" width="8" height="8" transform="rotate(45 6 6)" />,
  'at-risk': <path d="M6 1.2 11 10.5H1z" />,
};

export default function RiskBadge({ category }: { category: RiskCategory }) {
  return (
    <span className={`badge badge-${category}`}>
      <svg viewBox="0 0 12 12" width="12" height="12" aria-hidden="true">
        {GLYPH[category]}
      </svg>
      {CATEGORY_LABEL[category]}
    </span>
  );
}
