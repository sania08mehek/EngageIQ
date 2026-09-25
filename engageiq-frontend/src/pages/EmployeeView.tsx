import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { api } from '../api/client';
import { useAsync } from '../hooks/useAsync';
import { Breadcrumb, ErrorState, Loading, SampleNotice } from '../components/States';
import RiskBadge from '../components/RiskBadge';
import TrendChart from '../components/TrendChart';
import ReviewPanel from '../components/ReviewPanel';
import { f2, num, signed } from '../lib/format';
import { featureChange, type FeatureReading, type TrendDirection } from '../lib/pace';

const TREND_TEXT: Record<TrendDirection, string> = { up: 'rising', flat: 'steady', down: 'falling' };

function FeatureTable({
  title,
  tone,
  rows,
}: {
  title: string;
  tone: 'ehs' | 'opi';
  rows: FeatureReading[];
}) {
  return (
    <div className="feature-table" style={{ marginBottom: '1.5rem' }}>
      <h3 className={`feature-title t-${tone}`}>{title}</h3>
      <div className="table-scroll">
        <table className="table table-tight">
          <thead>
            <tr>
              <th scope="col">Measure</th>
              <th scope="col" className="num">Last 4 weeks</th>
              <th scope="col" className="num">Their usual baseline</th>
              <th scope="col" className="num">Change</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((f) => {
              const c = featureChange(f);
              return (
                <tr key={f.key}>
                  <th scope="row">{f.label}</th>
                  <td className="num">
                    {num(f.value, f.decimals)}
                    {f.unit === '%' ? '%' : <> <span className="unit">{f.unit}</span></>}
                  </td>
                  <td className="num">{num(f.baseline, f.decimals)}</td>
                  <td className={`num chg chg-${c.tone}`}>
                    {c.label}
                    {c.tone !== 'neutral' && <span className="sr-only"> ({c.tone})</span>}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default function EmployeeView() {
  const { employeeId = '' } = useParams();
  const { data, error, reload } = useAsync(() => api.employee(employeeId), [employeeId]);
  const [copied, setCopied] = useState(false);

  if (error) return <ErrorState message={error} onRetry={reload} />;
  if (!data) return <Loading />;

  const { employee: e, risk, latest } = data;

  const handleCopySummary = () => {
    const text = [
      `EngageIQ Summary for ${e.name} (${e.roleName}, ${e.teamName})`,
      `PACE: ${f2(latest.pace)} (${risk.category.toUpperCase()}) | EHS: ${f2(latest.ehs)} | OPI: ${f2(latest.opi)}`,
      `Trend: ${TREND_TEXT[risk.trend]} (${signed(data.delta)} vs 4 weeks ago)`,
      `Risk Assessment: ${risk.summary}`,
      risk.patterns.length > 0 ? `Patterns: ${risk.patterns.map((p) => p.title).join('; ')}` : '',
    ]
      .filter(Boolean)
      .join('\n');

    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  return (
    <div className="wrap page">
      <Breadcrumb
        items={[
          { label: 'Organization', to: '/dashboard' },
          { label: e.teamName, to: `/dashboard/teams/${e.teamId}` },
          { label: e.name },
        ]}
      />

      <header className="person-head">
        <div>
          <h1>{e.name}</h1>
          <p className="muted">
            {e.roleName} on {e.teamName} · Evaluated against own history
          </p>
          <SampleNotice />
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem', flexWrap: 'wrap' }}>
          <button
            type="button"
            className="btn btn-ghost btn-sm"
            onClick={handleCopySummary}
            aria-label="Copy summary to clipboard"
          >
            {copied ? '✓ Copied Summary' : '📋 Copy Summary'}
          </button>

          <div className="person-score">
            <div className="person-score-num">{f2(latest.pace)}</div>
            <div className="person-score-meta">
              <span>PACE Score</span>
              <RiskBadge category={risk.category} />
              <span
                className={`mini-delta ${
                  data.delta < -0.005 ? 'down' : data.delta > 0.005 ? 'up' : ''
                }`}
              >
                {signed(data.delta)} vs 4 weeks ago
              </span>
            </div>
          </div>
        </div>
      </header>

      <div className="person-grid">
        <div className="person-main">
          <section className="block" aria-labelledby="p-trend-h">
            <div className="block-head">
              <h2 id="p-trend-h">PACE over 12 weeks</h2>
              <span className="muted fineprint">Dashed line = {e.name.split(' ')[0]}&apos;s own usual baseline</span>
            </div>
            <div className="panel">
              <TrendChart data={data.history} baseline={data.baselinePace} />
            </div>
          </section>

          <section className="block" aria-labelledby="p-feat-h">
            <div className="block-head">
              <h2 id="p-feat-h">What is behind the score</h2>
            </div>
            <p className="muted" style={{ marginBottom: '1.25rem' }}>
              The last 4 weeks against {e.name.split(' ')[0]}&apos;s own usual level. Output measures are calibrated to fit the role ({e.roleName}).
            </p>
            <FeatureTable
              title="How work happens (EHS · 40%)"
              tone="ehs"
              rows={data.features.filter((f) => f.layer === 'signal')}
            />
            <FeatureTable
              title="What is delivered (OPI · 60%)"
              tone="opi"
              rows={data.features.filter((f) => f.layer === 'output')}
            />
          </section>
        </div>

        <aside className="person-side">
          <section className="panel explain" aria-labelledby="why-h">
            <h2 id="why-h">Pattern Insights</h2>
            {risk.patterns.length === 0 ? (
              <p>{risk.summary}</p>
            ) : (
              <ul className="patterns">
                {risk.patterns.map((p) => (
                  <li key={p.id}>
                    <strong>{p.title}</strong>
                    <p>{p.detail}</p>
                  </li>
                ))}
              </ul>
            )}

            <h3>Contributing Signals</h3>
            {risk.contributing.length === 0 ? (
              <p className="muted">Nothing has moved significantly from their usual pattern.</p>
            ) : (
              <ul className="changes">
                {risk.contributing.map((c) => (
                  <li key={c.key}>
                    <strong className={`t-${c.layer === 'signal' ? 'ehs' : 'opi'}`}>{c.label}</strong>
                    <span>{c.text}</span>
                  </li>
                ))}
              </ul>
            )}

            <p className="fineprint">
              Trend is {TREND_TEXT[risk.trend]}, based on {risk.evidenceWeeks} weeks of history. Risk score {f2(risk.riskScore)}. This is an indicator to look into, never an automated verdict.
            </p>
          </section>

          <ReviewPanel
            employeeId={e.id}
            status={data.reviewStatus}
            reviews={data.reviews}
            onSaved={reload}
          />
        </aside>
      </div>
    </div>
  );
}
