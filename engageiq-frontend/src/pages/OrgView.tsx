import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/client';
import { useAsync } from '../hooks/useAsync';
import { ErrorState, Loading, SampleNotice } from '../components/States';
import Stat from '../components/Stat';
import RiskBar from '../components/RiskBar';
import Sparkline from '../components/Sparkline';
import TrendChart from '../components/TrendChart';
import ReviewQueue from '../components/ReviewQueue';
import { classify } from '../lib/pace';
import { f2, longDate, signed } from '../lib/format';
import type { TeamRow } from '../api/types';

type SortField = 'name' | 'headcount' | 'pace' | 'ehs' | 'opi' | 'delta';
type QueueFilter = 'all' | 'needs-review' | 'reviewed';

export default function OrgView() {
  const { data, error, reload } = useAsync(() => api.organization(), []);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortField, setSortField] = useState<SortField>('pace');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [queueFilter, setQueueFilter] = useState<QueueFilter>('all');

  const filteredTeams = useMemo(() => {
    if (!data) return [];
    let list = data.teams.filter((t) =>
      t.team.name.toLowerCase().includes(searchTerm.toLowerCase()),
    );

    list.sort((a: TeamRow, b: TeamRow) => {
      let valA: number | string = 0;
      let valB: number | string = 0;
      switch (sortField) {
        case 'name':
          valA = a.team.name.toLowerCase();
          valB = b.team.name.toLowerCase();
          break;
        case 'headcount':
          valA = a.headcount;
          valB = b.headcount;
          break;
        case 'pace':
          valA = a.latest.pace;
          valB = b.latest.pace;
          break;
        case 'ehs':
          valA = a.latest.ehs;
          valB = b.latest.ehs;
          break;
        case 'opi':
          valA = a.latest.opi;
          valB = b.latest.opi;
          break;
        case 'delta':
          valA = a.delta;
          valB = b.delta;
          break;
      }
      if (valA < valB) return sortOrder === 'asc' ? -1 : 1;
      if (valA > valB) return sortOrder === 'asc' ? 1 : -1;
      return 0;
    });

    return list;
  }, [data, searchTerm, sortField, sortOrder]);

  const filteredQueue = useMemo(() => {
    if (!data) return [];
    if (queueFilter === 'all') return data.queue;
    return data.queue.filter((q) => q.status === queueFilter);
  }, [data, queueFilter]);

  if (error) return <ErrorState message={error} onRetry={reload} />;
  if (!data) return <Loading />;

  const { history, latest } = data;
  const before = history[history.length - 5];
  const waiting = data.queue.filter((q) => q.status === 'needs-review').length;

  function toggleSort(field: SortField) {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('desc');
    }
  }

  function renderSortIndicator(field: SortField) {
    if (sortField !== field) return null;
    return <span className="sort-indicator">{sortOrder === 'asc' ? '↑' : '↓'}</span>;
  }

  return (
    <div className="wrap page">
      <header className="page-head">
        <h1>Organization Health & Performance</h1>
        <p className="muted">
          {data.headcount} people across {data.teams.length} teams, 12 weeks up to the week of {longDate(latest.week)}.
        </p>
        <SampleNotice />
      </header>

      <div className="stats">
        <Stat label="PACE (Composite)" value={f2(latest.pace)} delta={data.delta} />
        <Stat
          label="Work-pattern health (EHS)"
          value={f2(latest.ehs)}
          delta={latest.ehs - before.ehs}
          tone="ehs"
        />
        <Stat
          label="Output deliverables (OPI)"
          value={f2(latest.opi)}
          delta={latest.opi - before.opi}
          tone="opi"
        />
        <div className="stat">
          <div className="stat-label">Risk distribution</div>
          <RiskBar mix={data.mix} legend />
        </div>
      </div>

      <section className="block" aria-labelledby="trend-h">
        <div className="block-head">
          <h2 id="trend-h">12-Week Organization Trend</h2>
          <span className="muted fineprint">Composite PACE = 0.4 × EHS + 0.6 × OPI</span>
        </div>
        <div className="panel">
          <TrendChart data={history} />
        </div>
      </section>

      <div className="split">
        <section className="block" aria-labelledby="teams-h">
          <div className="block-head">
            <h2 id="teams-h">Teams ({data.teams.length})</h2>
          </div>

          <div className="table-controls">
            <div className="table-search">
              <svg
                className="search-icon"
                viewBox="0 0 20 20"
                width="16"
                height="16"
                fill="currentColor"
                aria-hidden="true"
              >
                <path
                  fillRule="evenodd"
                  d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z"
                  clipRule="evenodd"
                />
              </svg>
              <input
                type="search"
                placeholder="Filter teams..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                aria-label="Filter teams"
              />
            </div>
            <span className="muted fineprint">
              Showing {filteredTeams.length} of {data.teams.length}
            </span>
          </div>

          <div className="table-scroll">
            <table className="table">
              <thead>
                <tr>
                  <th scope="col" className="sortable" onClick={() => toggleSort('name')}>
                    Team {renderSortIndicator('name')}
                  </th>
                  <th scope="col" className="num sortable" onClick={() => toggleSort('headcount')}>
                    People {renderSortIndicator('headcount')}
                  </th>
                  <th scope="col" className="num sortable" onClick={() => toggleSort('pace')}>
                    PACE {renderSortIndicator('pace')}
                  </th>
                  <th scope="col" className="num sortable" onClick={() => toggleSort('ehs')}>
                    EHS {renderSortIndicator('ehs')}
                  </th>
                  <th scope="col" className="num sortable" onClick={() => toggleSort('opi')}>
                    OPI {renderSortIndicator('opi')}
                  </th>
                  <th scope="col">Last 8 wks</th>
                  <th scope="col">Risk mix</th>
                </tr>
              </thead>
              <tbody>
                {filteredTeams.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="muted" style={{ textAlign: 'center', padding: '2rem' }}>
                      No teams match &ldquo;{searchTerm}&rdquo;
                    </td>
                  </tr>
                ) : (
                  filteredTeams.map((t) => (
                    <tr key={t.team.id}>
                      <th scope="row">
                        <Link to={`/dashboard/teams/${t.team.id}`}>{t.team.name}</Link>
                      </th>
                      <td className="num">{t.headcount}</td>
                      <td className="num">
                        <strong>{f2(t.latest.pace)}</strong>{' '}
                        <span
                          className={`mini-delta ${
                            t.delta < -0.005 ? 'down' : t.delta > 0.005 ? 'up' : ''
                          }`}
                        >
                          {signed(t.delta)}
                        </span>
                      </td>
                      <td className="num">{f2(t.latest.ehs)}</td>
                      <td className="num">{f2(t.latest.opi)}</td>
                      <td>
                        <Sparkline values={t.sparkline} category={classify(t.latest.pace)} />
                      </td>
                      <td className="mixcell">
                        <RiskBar mix={t.mix} />
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </section>

        <section className="block" aria-labelledby="queue-h">
          <div className="block-head">
            <h2 id="queue-h">Review Queue</h2>
            <div className="filter-pills">
              <button
                type="button"
                className={`filter-pill ${queueFilter === 'all' ? 'active' : ''}`}
                onClick={() => setQueueFilter('all')}
              >
                All ({data.queue.length})
              </button>
              <button
                type="button"
                className={`filter-pill ${queueFilter === 'needs-review' ? 'active' : ''}`}
                onClick={() => setQueueFilter('needs-review')}
              >
                Waiting ({waiting})
              </button>
              <button
                type="button"
                className={`filter-pill ${queueFilter === 'reviewed' ? 'active' : ''}`}
                onClick={() => setQueueFilter('reviewed')}
              >
                Reviewed ({data.queue.length - waiting})
              </button>
            </div>
          </div>

          <p className="muted queue-count">
            {waiting === 0
              ? 'All flagged patterns have been human-reviewed.'
              : `${waiting} pattern${waiting > 1 ? 's' : ''} waiting for manager review.`}
          </p>
          <ReviewQueue items={filteredQueue} />
        </section>
      </div>
    </div>
  );
}
