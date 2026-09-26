import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import DualLens from '../components/DualLens';
import UploadModal from '../components/UploadModal';

const STEPS = [
  { name: 'Collect', text: 'Pull calendar, task and code metadata through official APIs.' },
  { name: 'Normalize', text: 'Clean it, drop what is not needed and anonymize it.' },
  { name: 'Measure', text: 'Turn events into work-pattern and output features.' },
  { name: 'Score', text: 'Combine EHS and OPI into one PACE score.' },
  { name: 'Detect trends', text: 'Compare each person with their own history.' },
  { name: 'Flag risk', text: 'Classify as Healthy, Moderate or At-risk, with reasons.' },
  { name: 'Human review', text: 'A manager adds context and decides what, if anything, to do.' },
];

const USES = [
  'Meeting counts and durations',
  'Reply timing, not message contents',
  'Task and sprint records',
  'Commit and pull request counts',
  'Effort the person reports themselves',
];

const NEVER = [
  'Keystrokes',
  'Screenshots or screen recording',
  'Webcam',
  'Message contents',
  'Personal browsing',
];

function Tick() {
  return (
    <svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true">
      <path d="M3 8.5 6.5 12 13 4.5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function Cross() {
  return (
    <svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true">
      <path d="M4 4l8 8M12 4l-8 8" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

export default function Home() {
  const [isUploadOpen, setIsUploadOpen] = useState(false);

  return (
    <>
      {isUploadOpen && <UploadModal onClose={() => setIsUploadOpen(false)} onSuccess={() => {}} />}
      <section className="wrap hero">
        <div className="hero-copy">
          <h1>See how work is going, not who is online.</h1>
          <p className="lead">
            EngageIQ turns calendar and delivery metadata into one score and a trend. When a pattern changes, a person takes a look. Nothing is decided automatically.
          </p>
          <div className="actions">
            <button className="btn" onClick={() => setIsUploadOpen(true)}>Get Started (Upload Data)</button>
            <Link className="btn btn-ghost" to="/pace-score">Try the PACE score</Link>
          </div>
        </div>
        <figure className="hero-lens">
          <DualLens ehs={0.5} opi={0.8} />
          <figcaption>
            Circle size shows weight. Filled area shows the score. Here 0.4 × 0.50 + 0.6 × 0.80 = 0.68, which is Moderate.
          </figcaption>
        </figure>
      </section>

      <section className="wrap formula-band" aria-label="The PACE formula">
        <p className="formula">
          PACE = 0.4 × <span className="t-ehs">EHS</span> + 0.6 × <span className="t-opi">OPI</span>
        </p>
        <p className="formula-note">
          Output counts for more than work patterns, so people who collaborate quietly are not penalized for it.
        </p>
      </section>

      <section className="wrap section" aria-labelledby="lenses-h">
        <h2 id="lenses-h">Two lenses on the same work</h2>
        <div className="lenses">
          <article className="lens-card lens-card-ehs">
            <h3>How work happens</h3>
            <p className="weight">EHS, 40% of the score</p>
            <p>The health of work habits, read from calendar and messaging metadata.</p>
            <ul>
              <li>Meeting load</li>
              <li>Focus-time gaps</li>
              <li>Response time</li>
              <li>After-hours activity</li>
            </ul>
          </article>
          <article className="lens-card lens-card-opi">
            <h3>What is delivered</h3>
            <p className="weight">OPI, 60% of the score</p>
            <p>Actual outcomes from project and code tools, read against each role's own kind of work.</p>
            <ul className="two-col">
              <li>Task completion</li>
              <li>Sprint velocity</li>
              <li>Deadline adherence</li>
              <li>Commits and pull requests</li>
              <li>Self-reported effort</li>
              <li>Rework</li>
            </ul>
          </article>
        </div>
      </section>

      <section className="wrap section pipeline" aria-labelledby="flow-h">
        <div className="pipeline-intro">
          <h2 id="flow-h">From data to a decision you make</h2>
          <p>
            Every step is built so the last one stays human. The system measures, scores and flags. A manager decides.
          </p>
        </div>
        <ol className="steps">
          {STEPS.map((s) => (
            <li key={s.name}>
              <h3>{s.name}</h3>
              <p>{s.text}</p>
            </li>
          ))}
        </ol>
      </section>

      <section className="wrap section" aria-labelledby="privacy-h">
        <h2 id="privacy-h">What it reads and what it never touches</h2>
        <div className="boundary">
          <div>
            <h3>Reads</h3>
            <ul className="marks marks-yes">
              {USES.map((u) => (
                <li key={u}><Tick />{u}</li>
              ))}
            </ul>
          </div>
          <div>
            <h3>Never touches</h3>
            <ul className="marks marks-no">
              {NEVER.map((u) => (
                <li key={u}><Cross />{u}</li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      <section className="wrap section" aria-labelledby="bands-h">
        <h2 id="bands-h">How scores are read</h2>
        <div className="bands" role="img" aria-label="Score bands: At-risk 0.00 to 0.40, Moderate 0.40 to 0.70, Healthy 0.70 to 1.00">
          <div className="band band-at-risk" style={{ flexGrow: 40 }}><strong>At-risk</strong><span>0.00 to 0.40</span></div>
          <div className="band band-moderate" style={{ flexGrow: 30 }}><strong>Moderate</strong><span>0.40 to 0.70</span></div>
          <div className="band band-healthy" style={{ flexGrow: 30 }}><strong>Healthy</strong><span>0.70 to 1.00</span></div>
        </div>
        <p className="muted">
          A score is never read alone. Each one comes with a trend, the measures behind it and an explanation. These bands are a starting point to check against your own data before anyone acts on them.
        </p>
      </section>

      <section className="wrap section closing">
        <h2>Look at a sample team</h2>
        <p>The dashboard shows an organization, its teams and each person, with the review queue a manager works through.</p>
        <button className="btn" onClick={() => setIsUploadOpen(true)}>Upload Data</button>
      </section>
    </>
  );
}
