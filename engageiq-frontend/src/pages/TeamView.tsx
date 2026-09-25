import { useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { api } from '../api/client';
import { useAsync } from '../hooks/useAsync';
import { Breadcrumb, ErrorState, Loading, SampleNotice } from '../components/States';
import Stat from '../components/Stat';
import RiskBar from '../components/RiskBar';
import RiskBadge from '../components/RiskBadge';
import Sparkline from '../components/Sparkline';
import TrendChart from '../components/TrendChart';
import ReviewQueue from '../components/ReviewQueue';
import { f2, signed } from '../lib/format';
import type { EmployeeRow, ReviewStatus } from '../api/types';
import type { RiskCategory } from '../lib/pace';

const STATUS_TEXT: Record<ReviewStatus, string> = {
  'not-flagged': 'Nothing flagged',
  'needs-review': 'Needs review',
  reviewed: 'Reviewed',
};

type SortField = 'name' | 'pace' | 'delta' | 'ehs' | 'opi';

export default function TeamView() {
  const { teamId = '' } = useParams();
  const { data, error, reload } = useAsync(() => api.team(teamId), [teamId]);

  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<RiskCategory | 'all'>('all');
  const [selectedStatus, setSelectedStatus] = useState<ReviewStatus | 'all'>('all');
  const [sortField, setSortField] = useState<SortField>('pace');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  const filteredMembers = useMemo(() => {
    if (!data) return [];
    let list = data.members.filter((m) => {
      const matchSearch =
        m.employee.name.toLowerCase().includes(search.toLowerCase()) ||
        m.employee.roleName.toLowerCase().includes(search.toLowerCase());
      const matchCat = selectedCategory === 'all' || m.category === selectedCategory;
      const matchStatus = selectedStatus === 'all' || m.reviewStatus === selectedStatus;
      return matchSearch && matchCat && matchStatus;
    });

    list.sort((a: EmployeeRow, b: EmployeeRow) => {
      let valA: number | string = 0;
      let valB: number | string = 0;
      switch (sortField) {
        case 'name':
          valA = a.employee.name.toLowerCase();
          valB = b.employee.name.toLowerCase();
          break;
        case 'pace':
          valA = a.latest.pace;
          valB = b.latest.pace;
          break;
        case 'delta':
          valA = a.delta;
          valB = b.delta;
          break;
        case 'ehs':
          valA = a.latest.ehs;
          valB = b.latest.ehs;
          break;
        case 'opi':
          valA = a.latest.opi;
          valB = b.latest.opi;
          break;
      }
      if (valA < valB) return sortOrder === 'asc' ? -1 : 1;
      if (valA > valB) return sortOrder === 'asc' ? 1 : -1;
      return 0;
    });

    return list;
  }, [data, search, selectedCategory, selectedStatus, sortField, sortOrder]);

  if (error) return <ErrorState message={error} onRetry={reload} />;
  if (!data) return <Loading />;

  const { history, latest } = data;
  const before = history[history.length - 5];

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
      <Breadcrumb
        items={[{ label: 'Organization', to: '/dashboard' }, { label: data.team.name }]}
      />
      <header className="page-head">
        <h1>{data.team.name} Team</h1>
        <p className="muted">
          {data.headcount} team members · Trend against role-specific baselines
        </p>
        <SampleNotice />
      </header>

      <div className="stats">
        <Stat label="Team PACE" value={f2(latest.pace)} delta={data.delta} />
        <Stat
          label="Work-pattern health (EHS)"
          value={f2(latest.ehs)}
          delta={latest.ehs - before.ehs}
          tone="ehs"
        />
        <Stat
          label="Output (OPI)"
          value={f2(latest.opi)}
          delta={latest.opi - before.opi}
          tone="opi"
        />
        <div className="stat">
          <div className="stat-label">Risk distribution</div>
          <RiskBar mix={data.mix} legend />
        </div>
      </div>

      <section className="block" aria-labelledby="team-trend-h">
        <div className="block-head">
          <h2 id="team-trend-h">Team Trend (12 Weeks)</h2>
          <span className="muted fineprint">Weekly aggregate across all members</span>
        </div>
        <div className="panel">
          <TrendChart data={history} />
        </div>
      </section>

      <section className="block" aria-labelledby="members-h">
        <div className="block-head">
          <div>
            <h2 id="members-h">Team Members ({data.members.length})</h2>
            <p className="muted" style={{ margin: '0.25rem 0 0' }}>
              Compared with four weeks ago. Individual roles are read against their own baseline, not one shared standard.
            </p>
          </div>
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
              placeholder="Search by name or role..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              aria-label="Search members"
            />
          </div>

          <div className="filter-pills">
            <button
              type="button"
              className={`filter-pill ${selectedCategory === 'all' ? 'active' : ''}`}
              onClick={() => setSelectedCategory('all')}
            >
              All Categories
            </button>
            <button
              type="button"
              className={`filter-pill ${selectedCategory === 'healthy' ? 'active' : ''}`}
              onClick={() => setSelectedCategory('healthy')}
            >
              Healthy ({data.mix.healthy})
            </button>
            <button
              type="button"
              className={`filter-pill ${selectedCategory === 'moderate' ? 'active' : ''}`}
              onClick={() => setSelectedCategory('moderate')}
            >
              Moderate ({data.mix.moderate})
            </button>
            <button
              type="button"
              className={`filter-pill ${selectedCategory === 'at-risk' ? 'active' : ''}`}
              onClick={() => setSelectedCategory('at-risk')}
            >
              At-Risk ({data.mix['at-risk']})
            </button>
          </div>
        </div>

        <div className="table-scroll">
          <table className="table">
            <thead>
              <tr>
                <th scope="col" className="sortable" onClick={() => toggleSort('name')}>
                  Person {renderSortIndicator('name')}
                </th>
                <th scope="col" className="num sortable" onClick={() => toggleSort('pace')}>
                  PACE {renderSortIndicator('pace')}
                </th>
                <th scope="col" className="num sortable" onClick={() => toggleSort('delta')}>
                  Change {renderSortIndicator('delta')}
                </th>
                <th scope="col" className="num sortable" onClick={() => toggleSort('ehs')}>
                  EHS {renderSortIndicator('ehs')}
                </th>
                <th scope="col" className="num sortable" onClick={() => toggleSort('opi')}>
                  OPI {renderSortIndicator('opi')}
                </th>
                <th scope="col">Last 8 wks</th>
                <th scope="col">Category</th>
                <th scope="col">Review Status</th>
              </tr>
            </thead>
            <tbody>
              {filteredMembers.length === 0 ? (
                <tr>
                  <td colSpan={8} className="muted" style={{ textAlign: 'center', padding: '2rem' }}>
                    No team members match current search and filters.
                  </td>
                </tr>
              ) : (
                filteredMembers.map((m) => (
                  <tr key={m.employee.id}>
                    <th scope="row">
                      <Link to={`/dashboard/people/${m.employee.id}`}>{m.employee.name}</Link>
                      <span className="cell-sub">{m.employee.roleName}</span>
                    </th>
                    <td className="num">
                      <strong>{f2(m.latest.pace)}</strong>
                    </td>
                    <td
                      className={`num mini-delta ${
                        m.delta < -0.005 ? 'down' : m.delta > 0.005 ? 'up' : ''
                      }`}
                    >
                      {signed(m.delta)}
                    </td>
                    <td className="num">{f2(m.latest.ehs)}</td>
                    <td className="num">{f2(m.latest.opi)}</td>
                    <td>
                      <Sparkline values={m.sparkline} category={m.category} />
                    </td>
                    <td>
                      <RiskBadge category={m.category} />
                    </td>
                    <td>
                      <span className={`status status-${m.reviewStatus}`}>
                        {STATUS_TEXT[m.reviewStatus]}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>

      {data.queue.length > 0 && (
        <section className="block" aria-labelledby="team-queue-h">
          <div className="block-head">
            <h2 id="team-queue-h">Team Review Queue ({data.queue.length})</h2>
          </div>
          <ReviewQueue items={data.queue} />
        </section>
      )}
    </div>
  );
}
