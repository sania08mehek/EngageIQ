import { useState } from 'react';
import { api } from '../api/client';
import { useAsync } from '../hooks/useAsync';
import { ErrorState, Loading } from '../components/States';
import UploadModal from '../components/UploadModal';
import type { ConnectorInfo, MappedIdentity } from '../api/types';

export default function Integrations() {
  const { data, error, reload } = useAsync(() => api.integrationsStatus(), []);
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [syncingId, setSyncingId] = useState<string | null>(null);
  const [syncMessage, setSyncMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);
  const [activeTab, setActiveTab] = useState<'connectors' | 'identities' | 'webhook-test'>('connectors');

  // Webhook Test State
  const [webhookSource, setWebhookSource] = useState<'slack' | 'github' | 'jira'>('github');
  const [webhookPayload, setWebhookPayload] = useState<string>(JSON.stringify({
    action: "push",
    sender: { login: "alex-chen" },
    repository: { name: "engageiq-core" },
    commits: [{ id: "c101", message: "feat: add real-time telemetry streaming" }]
  }, null, 2));
  const [webhookResult, setWebhookResult] = useState<any>(null);
  const [isSendingWebhook, setIsSendingWebhook] = useState(false);

  if (error) return <ErrorState message={error} onRetry={reload} />;
  if (!data) return <Loading />;

  const handleSyncAll = async () => {
    setSyncingId('all');
    setSyncMessage(null);
    try {
      const res = await api.runAggregation(7);
      setSyncMessage({
        text: `Successfully aggregated telemetry across ${res.length} employees and updated SQLite database with latest 40:60 PACE scores!`,
        type: 'success',
      });
      reload();
    } catch (err: any) {
      setSyncMessage({ text: `Aggregation failed: ${err.message}`, type: 'error' });
    } finally {
      setSyncingId(null);
    }
  };

  const handleSyncSingle = async (connectorId: string) => {
    setSyncingId(connectorId);
    setSyncMessage(null);
    try {
      await api.syncConnector(connectorId);
      setSyncMessage({
        text: `Connector '${connectorId}' synced and employee metrics updated.`,
        type: 'success',
      });
      reload();
    } catch (err: any) {
      setSyncMessage({ text: `Sync failed: ${err.message}`, type: 'error' });
    } finally {
      setSyncingId(null);
    }
  };

  const handleSendTestWebhook = async () => {
    setIsSendingWebhook(true);
    setWebhookResult(null);
    try {
      const parsed = JSON.parse(webhookPayload);
      const res = await api.sendWebhook(webhookSource, parsed);
      setWebhookResult({ status: 'success', data: res });
    } catch (err: any) {
      setWebhookResult({ status: 'error', message: err.message });
    } finally {
      setIsSendingWebhook(false);
    }
  };

  const handleWebhookSourceChange = (src: 'slack' | 'github' | 'jira') => {
    setWebhookSource(src);
    if (src === 'github') {
      setWebhookPayload(JSON.stringify({
        action: "push",
        sender: { login: "alex-chen" },
        repository: { name: "engageiq-core" },
        commits: [{ id: "c101", message: "feat: add real-time telemetry streaming" }]
      }, null, 2));
    } else if (src === 'slack') {
      setWebhookPayload(JSON.stringify({
        event: {
          type: "message",
          user: "U_SARAH",
          text: "Hey team, PR review is ready for testing",
          ts: "1729700000.000100"
        }
      }, null, 2));
    } else {
      setWebhookPayload(JSON.stringify({
        webhookEvent: "jira:issue_updated",
        issue: {
          key: "ENG-402",
          fields: {
            assignee: { accountId: "acc_marcus" },
            status: { name: "Done" },
            customfield_10002: 5
          }
        }
      }, null, 2));
    }
  };

  return (
    <div className="wrap page">
      {isUploadOpen && (
        <UploadModal
          onClose={() => setIsUploadOpen(false)}
          onSuccess={() => {
            setSyncMessage({ text: 'CSV uploaded and processed into SQLite database.', type: 'success' });
            reload();
          }}
        />
      )}

      <header className="page-head" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1>Data Sources & Telemetry Integrations</h1>
          <p className="muted">
            Phase 2B Multi-Source Pipeline: Official connector modules for Calendar, Slack, Jira, GitHub, and CSV Ingestion.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
          <button
            className="btn btn-ghost"
            onClick={() => setIsUploadOpen(true)}
            title="Upload raw metadata CSV directly into the pipeline"
          >
            Upload CSV File
          </button>
          <button
            className="btn"
            onClick={handleSyncAll}
            disabled={syncingId !== null}
            style={{ minWidth: '210px' }}
          >
            {syncingId === 'all' ? 'Aggregating Telemetry...' : '⚡ Run Multi-Source Sync'}
          </button>
        </div>
      </header>

      {syncMessage && (
        <div style={{
          padding: '1rem 1.25rem',
          borderRadius: 'var(--r-md)',
          marginBottom: '1.5rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          backgroundColor: syncMessage.type === 'success' ? 'var(--healthy-wash)' : 'var(--at-risk-wash)',
          color: syncMessage.type === 'success' ? 'var(--healthy-text)' : 'var(--at-risk-text)',
          border: `1px solid ${syncMessage.type === 'success' ? 'var(--healthy)' : 'var(--at-risk)'}`
        }}>
          <div>
            <strong>{syncMessage.type === 'success' ? '✓ Pipeline Synchronized:' : '✕ Error:'}</strong>{' '}
            {syncMessage.text}
          </div>
          <button
            onClick={() => setSyncMessage(null)}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'inherit', fontWeight: 'bold' }}
          >
            ×
          </button>
        </div>
      )}

      {/* Tabs */}
      <div className="filter-pills" style={{ marginBottom: '1.5rem' }}>
        <button
          type="button"
          className={`filter-pill ${activeTab === 'connectors' ? 'active' : ''}`}
          onClick={() => setActiveTab('connectors')}
        >
          Data Connectors ({data.connectors.length})
        </button>
        <button
          type="button"
          className={`filter-pill ${activeTab === 'identities' ? 'active' : ''}`}
          onClick={() => setActiveTab('identities')}
        >
          Identity Resolver Directory ({data.mappedIdentitiesCount})
        </button>
        <button
          type="button"
          className={`filter-pill ${activeTab === 'webhook-test' ? 'active' : ''}`}
          onClick={() => setActiveTab('webhook-test')}
        >
          Webhook Receiver Test Console
        </button>
      </div>

      {/* TAB 1: DATA CONNECTORS */}
      {activeTab === 'connectors' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.25rem' }}>
          {data.connectors.map((connector: ConnectorInfo) => {
            const isSyncing = syncingId === connector.id;
            return (
              <div key={connector.id} className="panel" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                    <div>
                      <span style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--muted)', fontWeight: 600 }}>
                        {connector.category}
                      </span>
                      <h2 style={{ fontSize: '1.3rem', margin: '0.2rem 0' }}>{connector.name}</h2>
                    </div>
                    <span style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '0.4rem',
                      padding: '0.25rem 0.65rem',
                      borderRadius: '999px',
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      backgroundColor: 'var(--healthy-wash)',
                      color: 'var(--healthy-text)',
                      border: '1px solid var(--healthy)'
                    }}>
                      <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: 'var(--healthy)' }} />
                      {connector.status.toUpperCase()}
                    </span>
                  </div>

                  <p className="muted" style={{ fontSize: '0.9rem', marginBottom: '1rem', minHeight: '2.7rem' }}>
                    {connector.description}
                  </p>

                  <div style={{ padding: '0.75rem', backgroundColor: 'var(--wash)', borderRadius: 'var(--r-md)', marginBottom: '1rem', fontSize: '0.85rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
                      <span className="muted">Sync Mode:</span>
                      <strong>{connector.mode}</strong>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
                      <span className="muted">Buffered Events:</span>
                      <strong>{connector.bufferedEvents} events</strong>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span className="muted">Last Sync:</span>
                      <span>{new Date(connector.lastSync).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                    </div>
                  </div>

                  <div style={{ marginBottom: '1.25rem' }}>
                    <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--muted)', display: 'block', marginBottom: '0.4rem' }}>
                      METRICS EXTRACTED:
                    </span>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem' }}>
                      {connector.metrics.map((m) => (
                        <span key={m} style={{
                          fontSize: '0.75rem',
                          padding: '0.15rem 0.5rem',
                          backgroundColor: 'var(--panel)',
                          border: '1px solid var(--rule)',
                          borderRadius: 'var(--r-sm)',
                          color: 'var(--ink)'
                        }}>
                          {m}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

                <div style={{ borderTop: '1px solid var(--rule)', paddingTop: '1rem', display: 'flex', justifyContent: 'flex-end' }}>
                  {connector.id === 'csv' ? (
                    <button className="btn btn-sm btn-ghost" onClick={() => setIsUploadOpen(true)}>
                      Upload File
                    </button>
                  ) : (
                    <button
                      className="btn btn-sm"
                      onClick={() => handleSyncSingle(connector.id)}
                      disabled={isSyncing || syncingId !== null}
                    >
                      {isSyncing ? 'Syncing...' : 'Sync Now'}
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* TAB 2: IDENTITY RESOLUTION */}
      {activeTab === 'identities' && (
        <section className="block">
          <div className="block-head">
            <div>
              <h2>Cross-Source Identity Resolution Table</h2>
              <p className="muted" style={{ margin: '0.25rem 0 0' }}>
                Maps disparate SaaS usernames and OAuth IDs into normalized internal employee profiles for timezone-aware scoring.
              </p>
            </div>
          </div>
          <div className="table-scroll">
            <table className="table">
              <thead>
                <tr>
                  <th scope="col">Employee</th>
                  <th scope="col">Role & Team</th>
                  <th scope="col">GitHub Username</th>
                  <th scope="col">Jira Account ID</th>
                  <th scope="col">Slack User ID</th>
                  <th scope="col">Google Calendar</th>
                  <th scope="col">Timezone</th>
                  <th scope="col">Status</th>
                </tr>
              </thead>
              <tbody>
                {data.identities.map((identity: MappedIdentity) => (
                  <tr key={identity.employeeId}>
                    <td>
                      <strong>{identity.name}</strong>
                      <span className="muted fineprint" style={{ display: 'block' }}>{identity.employeeId}</span>
                    </td>
                    <td>
                      <span>{identity.role}</span>
                      <span className="muted fineprint" style={{ display: 'block' }}>{identity.team}</span>
                    </td>
                    <td><code>{identity.accounts.github || '—'}</code></td>
                    <td><code>{identity.accounts.jira || '—'}</code></td>
                    <td><code>{identity.accounts.slack || '—'}</code></td>
                    <td><span style={{ fontSize: '0.85rem' }}>{identity.accounts.calendar || '—'}</span></td>
                    <td><span className="muted" style={{ fontSize: '0.85rem' }}>{identity.timezone}</span></td>
                    <td>
                      <span style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '0.35rem',
                        fontSize: '0.75rem',
                        fontWeight: 600,
                        color: 'var(--healthy)'
                      }}>
                        ● Resolved
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {/* TAB 3: WEBHOOK RECEIVER TEST CONSOLE */}
      {activeTab === 'webhook-test' && (
        <section className="block">
          <div className="block-head">
            <div>
              <h2>Webhook Receiver Test Console</h2>
              <p className="muted" style={{ margin: '0.25rem 0 0' }}>
                Simulate inbound real-time events from GitHub, Slack, or Jira directly into the FastAPI webhook endpoints.
              </p>
            </div>
          </div>

          <div className="panel" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '2rem' }}>
            <div>
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', fontWeight: 600, marginBottom: '0.5rem' }}>Select Inbound Webhook Platform:</label>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  {(['github', 'slack', 'jira'] as const).map((src) => (
                    <button
                      key={src}
                      type="button"
                      className={`filter-pill ${webhookSource === src ? 'active' : ''}`}
                      onClick={() => handleWebhookSourceChange(src)}
                    >
                      {src.toUpperCase()} Endpoint
                    </button>
                  ))}
                </div>
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                  <label htmlFor="webhook-payload" style={{ fontWeight: 600 }}>Inbound Event Payload (JSON):</label>
                  <span className="muted fineprint">POST /api/integration/webhooks/{webhookSource}</span>
                </div>
                <textarea
                  id="webhook-payload"
                  rows={10}
                  value={webhookPayload}
                  onChange={(e) => setWebhookPayload(e.target.value)}
                  style={{
                    width: '100%',
                    fontFamily: 'monospace',
                    fontSize: '0.85rem',
                    padding: '0.75rem',
                    borderRadius: 'var(--r-md)',
                    border: '1px solid var(--rule)',
                    backgroundColor: 'var(--paper)',
                    color: 'var(--ink)'
                  }}
                />
              </div>

              <button
                className="btn"
                onClick={handleSendTestWebhook}
                disabled={isSendingWebhook}
              >
                {isSendingWebhook ? 'Dispatching Webhook...' : `Dispatch ${webhookSource.toUpperCase()} Webhook`}
              </button>
            </div>

            <div>
              <h3 style={{ marginBottom: '0.5rem' }}>FastAPI Receiver Response</h3>
              <p className="muted" style={{ fontSize: '0.85rem', marginBottom: '1rem' }}>
                Verified HTTP 200 acknowledgment with buffered event status.
              </p>
              {webhookResult ? (
                <pre style={{
                  padding: '1rem',
                  borderRadius: 'var(--r-md)',
                  backgroundColor: 'var(--wash)',
                  border: `1px solid ${webhookResult.status === 'success' ? 'var(--healthy)' : 'var(--at-risk)'}`,
                  fontSize: '0.85rem',
                  overflowX: 'auto',
                  maxHeight: '260px'
                }}>
                  {JSON.stringify(webhookResult, null, 2)}
                </pre>
              ) : (
                <div style={{
                  padding: '2.5rem',
                  borderRadius: 'var(--r-md)',
                  backgroundColor: 'var(--wash)',
                  textAlign: 'center',
                  color: 'var(--muted)',
                  fontSize: '0.9rem'
                }}>
                  Click &ldquo;Dispatch Webhook&rdquo; to send payload to the live server.
                </div>
              )}
            </div>
          </div>
        </section>
      )}
    </div>
  );
}
