import { useMemo, useState } from 'react';
import DualLens from '../components/DualLens';
import RiskBadge from '../components/RiskBadge';
import TrendChart from '../components/TrendChart';
import {
  clonePreset,
  computeIndices,
  OUTPUT_FEATURES,
  PRESETS,
  SIGNAL_FEATURES,
  type FeatureDef,
  type FeatureKey,
  type Inputs,
  type PresetId,
} from '../lib/features';
import { classify, detectPatterns, makeWeek, type RiskCategory } from '../lib/pace';
import { f2, num } from '../lib/format';

const WEEK_LABELS = ['Week 1', 'Week 2', 'Week 3', 'Week 4'];

const BAND_TEXT: Record<RiskCategory, string> = {
  healthy: 'Healthy: 0.70 and above',
  moderate: 'Moderate: 0.40 to 0.69',
  'at-risk': 'At-risk: below 0.40',
};

function SliderRow({
  def,
  value,
  onChange,
}: {
  def: FeatureDef;
  value: number;
  onChange: (v: number) => void;
}) {
  const id = `f-${def.key}`;
  const health = def.toHealth(value);
  const decimals = def.step < 1 ? 1 : 0;
  return (
    <div className="slider">
      <div className="slider-top">
        <label htmlFor={id}>{def.label}</label>
        <output htmlFor={id}>
          {num(value, decimals)} <span className="unit">{def.unit}</span>
        </output>
      </div>
      <input
        id={id}
        type="range"
        min={def.min}
        max={def.max}
        step={def.step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        aria-valuetext={`${num(value, decimals)} ${def.unit}`}
      />
      <div className="slider-foot">
        <span className="hint">{def.hint}</span>
        <span className="health" title="How healthy this reading is, from 0 to 1">
          <span className="health-bar">
            <i style={{ width: `${health * 100}%` }} />
          </span>
          {f2(health)}
        </span>
      </div>
    </div>
  );
}

export default function PaceScore() {
  const [presetId, setPresetId] = useState<PresetId>('slipping');
  const [weeks, setWeeks] = useState<Inputs[]>(() => clonePreset('slipping'));
  const [active, setActive] = useState(3);
  const [copied, setCopied] = useState(false);

  const scores = useMemo(() => weeks.map((w) => computeIndices(w)), [weeks]);
  const history = useMemo(
    () => scores.map((s, i) => makeWeek(`week-${i + 1}`, s.ehs, s.opi)),
    [scores],
  );
  const patterns = useMemo(() => detectPatterns(history), [history]);
  const now = scores[active];
  const category = classify(now.pace);

  function choose(id: PresetId) {
    setPresetId(id);
    setWeeks(clonePreset(id));
  }

  function setValue(key: FeatureKey, v: number) {
    setWeeks((ws) => ws.map((w, i) => (i === active ? { ...w, [key]: v } : w)));
  }

  const preset = PRESETS.find((p) => p.id === presetId);

  const handleCopyBreakdown = () => {
    const text = [
      `EngageIQ PACE Calculator (${WEEK_LABELS[active]})`,
      `Score: ${f2(now.pace)} (${category.toUpperCase()})`,
      `Formula: 0.4 × ${f2(now.ehs)} (EHS) + 0.6 × ${f2(now.opi)} (OPI) = ${f2(now.pace)}`,
      `Active Preset: ${preset?.name ?? 'Custom'}`,
      patterns.length > 0 ? `Detected Pattern: ${patterns.map((p) => p.title).join('; ')}` : 'No pattern flagged',
    ].join('\n');

    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  return (
    <div className="wrap page">
      <header className="page-head">
        <h1>Interactive PACE Simulator</h1>
        <p className="lead-sm">
          Adjust metadata readings for any week and watch how the work-pattern (EHS) and output (OPI) indices compose into the PACE score. Then inspect the 4-week window for multi-week risk patterns.
        </p>
      </header>

      <section className="block presets" aria-labelledby="start-h">
        <div className="block-head">
          <h2 id="start-h">Explore Real-World Scenarios</h2>
        </div>
        <div className="preset-list">
          {PRESETS.map((p) => (
            <button
              key={p.id}
              type="button"
              className="preset"
              aria-pressed={p.id === presetId}
              onClick={() => choose(p.id)}
            >
              <strong>{p.name}</strong>
              <span>{p.blurb}</span>
            </button>
          ))}
        </div>
      </section>

      <div className="calc-grid">
        <div className="calc-inputs">
          <div className="block-head" style={{ marginBottom: '0.75rem' }}>
            <h2>Select Week to Adjust</h2>
            <button
              type="button"
              className="btn btn-ghost btn-sm"
              onClick={() => choose(presetId)}
              title="Reset sliders to the initial scenario preset"
            >
              Reset to &ldquo;{preset?.name}&rdquo;
            </button>
          </div>

          <div className="week-picker" role="group" aria-label="Week you are editing">
            {WEEK_LABELS.map((label, i) => (
              <button
                key={label}
                type="button"
                aria-pressed={i === active}
                onClick={() => setActive(i)}
              >
                {label}
                <span>PACE {f2(scores[i].pace)}</span>
              </button>
            ))}
          </div>

          <fieldset className="layer layer-ehs">
            <legend>How Work Happens · EHS (40% weight)</legend>
            {SIGNAL_FEATURES.map((d) => (
              <SliderRow
                key={d.key}
                def={d}
                value={weeks[active][d.key]}
                onChange={(v) => setValue(d.key, v)}
              />
            ))}
          </fieldset>

          <fieldset className="layer layer-opi">
            <legend>What Is Delivered · OPI (60% weight)</legend>
            {OUTPUT_FEATURES.map((d) => (
              <SliderRow
                key={d.key}
                def={d}
                value={weeks[active][d.key]}
                onChange={(v) => setValue(d.key, v)}
              />
            ))}
          </fieldset>
        </div>

        <div className="calc-result">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h2 style={{ fontSize: '1.2rem', margin: 0 }}>{WEEK_LABELS[active]} Result</h2>
            <button
              type="button"
              className="btn btn-ghost btn-sm"
              onClick={handleCopyBreakdown}
              aria-label="Copy score breakdown"
            >
              {copied ? '✓ Copied' : '📋 Copy'}
            </button>
          </div>

          <DualLens ehs={now.ehs} opi={now.opi} />

          <p className="worked" aria-live="polite">
            0.4 × {f2(now.ehs)} + 0.6 × {f2(now.opi)} = <strong>{f2(now.pace)}</strong>
          </p>

          <div className="result-band">
            <RiskBadge category={category} />
            <span>{BAND_TEXT[category]}</span>
          </div>

          <p className="fineprint" style={{ textAlign: 'center', marginTop: '0.75rem' }}>
            Violet = EHS (40%) · Teal = OPI (60%). Circle area follows weight; filled area follows score.
          </p>
        </div>
      </div>

      <section className="block" aria-labelledby="four-h">
        <div className="block-head">
          <h2 id="four-h">4-Week Pattern Detection</h2>
          <span className="muted fineprint">PACE analyzes the moving window, not an isolated reading</span>
        </div>
        <div className="trend-grid">
          <div className="panel">
            <TrendChart data={history} labels={WEEK_LABELS} height={270} />
          </div>
          <div className="panel trend-check" aria-live="polite">
            <h3>Trend & Anomaly Check</h3>
            {patterns.length === 0 ? (
              <>
                <p>
                  <strong>No concerning pattern flagged.</strong>
                </p>
                <p className="muted">
                  These four weeks remain consistent with the role baseline, so no escalation or review is required.
                </p>
              </>
            ) : (
              <>
                <p>
                  <strong style={{ color: 'var(--moderate-text)' }}>A person should take a look.</strong>
                </p>
                <ul className="patterns">
                  {patterns.map((p) => (
                    <li key={p.id}>
                      <strong>{p.title}</strong>
                      <p>{p.detail}</p>
                    </li>
                  ))}
                </ul>
                <p className="fineprint">
                  PACE highlights patterns to invite human empathy and managerial support, never automated punitive action.
                </p>
              </>
            )}
          </div>
        </div>
      </section>
    </div>
  );
}
