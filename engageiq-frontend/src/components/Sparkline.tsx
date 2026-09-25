import { useTheme } from '../context/ThemeContext';
import { getRiskColors } from '../lib/colors';
import type { RiskCategory } from '../lib/pace';

interface Props {
  values: number[];
  category: RiskCategory;
  width?: number;
  height?: number;
}

/** Fixed 0.2 to 1.0 scale so slopes are comparable from row to row. */
export default function Sparkline({ values, category, width = 88, height = 26 }: Props) {
  const { theme } = useTheme();
  if (values.length < 2) return null;
  const x = (i: number) => 2 + (i / (values.length - 1)) * (width - 4);
  const y = (v: number) => height - 3 - ((Math.min(1, Math.max(0.2, v)) - 0.2) / 0.8) * (height - 6);
  const points = values.map((v, i) => `${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(' ');
  const riskColors = getRiskColors(theme);
  const color = riskColors[category];

  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      role="img"
      aria-label={`PACE over the last ${values.length} weeks`}
      className="sparkline-svg"
    >
      <polyline points={points} fill="none" stroke={color} strokeWidth="2.2" strokeLinejoin="round" strokeLinecap="round" />
      <circle cx={x(values.length - 1)} cy={y(values[values.length - 1])} r="3" fill={color} />
    </svg>
  );
}
