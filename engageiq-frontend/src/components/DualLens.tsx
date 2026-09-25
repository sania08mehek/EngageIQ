import { useTheme } from '../context/ThemeContext';
import { f2 } from '../lib/format';
import { CATEGORY_LABEL, classify, clamp01, paceScore } from '../lib/pace';

interface Props {
  ehs: number;
  opi: number;
}

// Circle area follows the weights (40 and 60). The filled disc inside each circle follows the score.
const A = { cx: 165, cy: 170, r: 94 };
const B = { cx: 280, cy: 170, r: 115 };

export default function DualLens({ ehs, opi }: Props) {
  const { colors, theme } = useTheme();
  const isDark = theme === 'dark';
  const pace = paceScore(ehs, opi);
  const label = `EHS ${f2(ehs)} at 40 percent weight and OPI ${f2(opi)} at 60 percent weight give a PACE score of ${f2(pace)}, ${CATEGORY_LABEL[classify(pace)]}.`;

  return (
    <svg className="lens" viewBox="55 6 355 290" role="img" aria-label={label}>
      <defs>
        <filter id="lens-glow" x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="0" dy="2" stdDeviation="4" floodColor={isDark ? '#000000' : '#8899a6'} floodOpacity={isDark ? '0.5' : '0.15'} />
        </filter>
      </defs>

      {/* Outer track circles */}
      <circle
        cx={A.cx}
        cy={A.cy}
        r={A.r}
        fill={colors.ehsWash}
        stroke={colors.ehs}
        strokeWidth="1.5"
        strokeDasharray={isDark ? '3 2' : undefined}
      />
      <circle
        cx={B.cx}
        cy={B.cy}
        r={B.r}
        fill={colors.opiWash}
        stroke={colors.opi}
        strokeWidth="1.5"
        strokeDasharray={isDark ? '3 2' : undefined}
      />

      {/* Dynamic filled score discs */}
      <circle
        className="lens-disc lens-disc-ehs"
        cx={A.cx}
        cy={A.cy}
        r={A.r * Math.sqrt(clamp01(ehs))}
        fill={colors.ehs}
        fillOpacity={isDark ? 0.75 : 0.82}
        style={{ mixBlendMode: isDark ? 'screen' : 'multiply' }}
      />
      <circle
        className="lens-disc lens-disc-opi lens-disc-b"
        cx={B.cx}
        cy={B.cy}
        r={B.r * Math.sqrt(clamp01(opi))}
        fill={colors.opi}
        fillOpacity={isDark ? 0.75 : 0.82}
        style={{ mixBlendMode: isDark ? 'screen' : 'multiply' }}
      />

      {/* Header labels */}
      <text x="118" y="24" textAnchor="middle" className="lens-name" fill={colors.ehs}>
        EHS {f2(ehs)}
      </text>
      <text x="118" y="43" textAnchor="middle" className="lens-sub" fill={colors.muted}>
        40% of score (Signals)
      </text>

      <text x="330" y="24" textAnchor="middle" className="lens-name" fill={colors.opi}>
        OPI {f2(opi)}
      </text>
      <text x="330" y="43" textAnchor="middle" className="lens-sub" fill={colors.muted}>
        60% of score (Outputs)
      </text>

      {/* Center composite PACE badge */}
      <g filter="url(#lens-glow)">
        <rect
          x="154"
          y="136"
          width="116"
          height="72"
          rx="14"
          fill={colors.panel}
          stroke={colors.rule}
          strokeWidth="1.5"
        />
        <text x="212" y="176" textAnchor="middle" className="lens-score" fill={colors.ink}>
          {f2(pace)}
        </text>
        <text x="212" y="196" textAnchor="middle" className="lens-pace" fill={colors.muted}>
          PACE Composite
        </text>
      </g>
    </svg>
  );
}
