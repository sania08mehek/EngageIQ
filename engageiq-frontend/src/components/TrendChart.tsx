import { CartesianGrid, Line, LineChart, ReferenceArea, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { useTheme } from '../context/ThemeContext';
import { f2, shortDate } from '../lib/format';
import type { WeeklyScore } from '../lib/pace';

interface Props {
  data: WeeklyScore[];
  /** Custom x labels, e.g. "Week 1". Defaults to the week's date. */
  labels?: string[];
  height?: number;
  /** Draws a dashed line at the person's own usual PACE */
  baseline?: number;
}

interface TipProps {
  active?: boolean;
  label?: string;
  payload?: { name?: string; value?: number; color?: string }[];
}

function ChartTip({ active, label, payload }: TipProps) {
  if (!active || !payload?.length) return null;
  return (
    <div className="chart-tip">
      <strong>{label}</strong>
      {payload.map((p) => (
        <div key={p.name} className="chart-tip-row">
          <i style={{ background: p.color }} />
          <span>{p.name}</span>
          <b>{f2(p.value ?? 0)}</b>
        </div>
      ))}
    </div>
  );
}

export default function TrendChart({ data, labels, height = 300, baseline }: Props) {
  const { colors, theme } = useTheme();

  const rows = data.map((w, i) => ({
    label: labels ? labels[i] : shortDate(w.week),
    PACE: Number(w.pace.toFixed(3)),
    EHS: Number(w.ehs.toFixed(3)),
    OPI: Number(w.opi.toFixed(3)),
  }));

  const tick = { fontSize: 12, fill: colors.muted };
  const band = (
    text: string,
    color: string,
    position: 'insideTopLeft' | 'insideBottomLeft' = 'insideBottomLeft',
  ) => ({
    value: text,
    position,
    fill: color,
    fontSize: 11,
    fontWeight: 600,
  });

  const areaOpacity = theme === 'dark' ? 0.12 : 0.08;

  return (
    <div className="chart">
      <ul className="chart-legend">
        <li>
          <i style={{ background: colors.ink }} />
          <span>PACE (Composite)</span>
        </li>
        <li>
          <i style={{ background: colors.ehs }} />
          <span>EHS (Work-pattern health)</span>
        </li>
        <li>
          <i style={{ background: colors.opi }} />
          <span>OPI (Output & deliverables)</span>
        </li>
      </ul>
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={rows} margin={{ top: 8, right: 14, bottom: 4, left: -12 }}>
          <ReferenceArea
            y1={0.7}
            y2={1}
            fill={colors.healthy}
            fillOpacity={areaOpacity}
            ifOverflow="hidden"
            label={band('Healthy', colors.healthyText, 'insideTopLeft')}
          />
          <ReferenceArea
            y1={0.4}
            y2={0.7}
            fill={colors.moderate}
            fillOpacity={areaOpacity}
            ifOverflow="hidden"
            label={band('Moderate', colors.moderateText)}
          />
          <ReferenceArea
            y1={0.2}
            y2={0.4}
            fill={colors.atRisk}
            fillOpacity={areaOpacity}
            ifOverflow="hidden"
            label={band('At-risk', colors.atRiskText)}
          />
          <CartesianGrid stroke={colors.gridLine} strokeDasharray="3 3" vertical={false} />
          <XAxis
            dataKey="label"
            tick={tick}
            tickLine={false}
            axisLine={{ stroke: colors.rule }}
            interval="preserveStartEnd"
          />
          <YAxis
            domain={[0.2, 1]}
            ticks={[0.2, 0.4, 0.7, 1]}
            tick={tick}
            tickLine={false}
            axisLine={false}
            tickFormatter={(v: number) => v.toFixed(1)}
          />
          {baseline !== undefined && (
            <ReferenceLine
              y={baseline}
              stroke={colors.muted}
              strokeDasharray="5 4"
              label={{
                value: 'Own usual',
                position: 'insideBottomRight',
                fill: colors.muted,
                fontSize: 11,
              }}
            />
          )}
          <Tooltip content={<ChartTip />} />
          <Line
            type="monotone"
            dataKey="EHS"
            stroke={colors.ehs}
            strokeWidth={2.2}
            dot={false}
            activeDot={{ r: 5, fill: colors.ehs }}
          />
          <Line
            type="monotone"
            dataKey="OPI"
            stroke={colors.opi}
            strokeWidth={2.2}
            dot={false}
            activeDot={{ r: 5, fill: colors.opi }}
          />
          <Line
            type="monotone"
            dataKey="PACE"
            stroke={colors.ink}
            strokeWidth={3}
            dot={false}
            activeDot={{ r: 6, fill: colors.ink }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
