import { useState, type FormEvent } from 'react';
import { api } from '../api/client';
import { outcomeLabel, REVIEW_OUTCOMES, type ReviewOutcome, type ReviewRecord, type ReviewStatus } from '../api/types';
import { longDate } from '../lib/format';

interface Props {
  employeeId: string;
  status: ReviewStatus;
  reviews: ReviewRecord[];
  onSaved: () => void;
}

const INTRO: Record<ReviewStatus, string> = {
  'needs-review': 'This pattern is waiting for a person to look at it. Add what you know, then choose what happens next.',
  reviewed: 'This week\'s flag has been reviewed. You can add another entry if things change.',
  'not-flagged': 'Nothing is flagged. You can still record a review, for example to correct a data issue.',
};

export default function ReviewPanel({ employeeId, status, reviews, onSaved }: Props) {
  const [outcome, setOutcome] = useState<ReviewOutcome | null>(null);
  const [note, setNote] = useState('');
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState('');

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (!outcome) return;
    setSaving(true);
    setError('');
    try {
      await api.submitReview({ employeeId, outcome, note });
      setOutcome(null);
      setNote('');
      setSaved(true);
      onSaved();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'The review was not saved.');
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="panel review" aria-labelledby="review-h">
      <h2 id="review-h">Human review</h2>
      <p className={`review-status review-${status}`}>{INTRO[status]}</p>

      <form onSubmit={submit}>
        <fieldset>
          <legend>What will you do?</legend>
          {REVIEW_OUTCOMES.map((o) => (
            <label key={o.id} className="choice">
              <input
                type="radio"
                name="outcome"
                value={o.id}
                checked={outcome === o.id}
                onChange={() => {
                  setOutcome(o.id);
                  setSaved(false);
                }}
              />
              <span>
                <strong>{o.label}</strong>
                <small>{o.hint}</small>
              </span>
            </label>
          ))}
        </fieldset>
        <label className="field">
          <span>Context (optional)</span>
          <textarea rows={3} value={note} onChange={(e) => setNote(e.target.value)} placeholder="What do you know that the numbers do not show?" />
        </label>
        <div className="actions">
          <button className="btn" type="submit" disabled={!outcome || saving}>{saving ? 'Saving' : 'Save review'}</button>
          {saved && <span role="status" className="saved">Review saved</span>}
        </div>
        {error && <p role="alert" className="form-error">{error}</p>}
      </form>

      <h3>History</h3>
      {reviews.length === 0 ? (
        <p className="muted">No reviews yet.</p>
      ) : (
        <ul className="history">
          {reviews.map((r) => (
            <li key={r.id}>
              <strong>{outcomeLabel(r.outcome)}</strong>
              <span className="muted">{longDate(r.at)}, {r.reviewer}</span>
              {r.note && <p>{r.note}</p>}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
