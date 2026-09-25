import React, { useState } from 'react';

export default function DataIngestion() {
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<string>('');
  const [results, setResults] = useState<any[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setFile(e.dataTransfer.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setStatus('Please select a file first.');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    setIsProcessing(true);
    setStatus('Processing metadata...');
    try {
      const response = await fetch('http://localhost:8000/api/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Upload failed');
      }

      const data = await response.json();
      setStatus(`Success! Processed ${data.processed_records} records.`);
      setResults(data.data);
    } catch (error: any) {
      setStatus(`Error: ${error.message}`);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="wrap page">
      <div className="page-head">
        <h1>Data Ingestion & Processing</h1>
        <p className="lead-sm">
          Upload historical work metadata to instantly calculate EHS, OPI, and PACE scores using our risk analysis engine.
        </p>
      </div>

      <div className="split" style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '2rem' }}>
        <section className="panel" style={{ position: 'relative', overflow: 'hidden' }}>
          {/* Glassmorphism accent background */}
          <div style={{
            position: 'absolute', top: '-50px', right: '-50px', width: '200px', height: '200px',
            background: 'var(--opi)', filter: 'blur(100px)', opacity: '0.15', borderRadius: '50%', zIndex: 0
          }}></div>
          
          <div style={{ position: 'relative', zIndex: 1 }}>
            <div className="block-head">
              <h2>Upload Work Metadata (CSV)</h2>
            </div>
            <p className="muted" style={{ marginBottom: '1.5rem' }}>
              In Phase 1 & 2, data ingestion is done via secure CSV uploads. Ensure your dataset includes 
              <code>meeting_load</code>, <code>focus_gap</code>, and <code>completion_rate</code> columns.
            </p>
            
            <div 
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              style={{
                border: `2px dashed ${isDragging ? 'var(--opi)' : 'var(--rule)'}`,
                borderRadius: 'var(--r-lg)',
                padding: '3rem 2rem',
                textAlign: 'center',
                backgroundColor: isDragging ? 'var(--opi-wash)' : 'var(--wash)',
                transition: 'all 0.3s ease',
                cursor: 'pointer',
                marginBottom: '1.5rem'
              }}
              onClick={() => document.getElementById('fileUpload')?.click()}
            >
              <input 
                id="fileUpload"
                type="file" 
                accept=".csv"
                onChange={handleFileChange}
                style={{ display: 'none' }}
              />
              <svg viewBox="0 0 24 24" width="48" height="48" stroke="var(--muted)" fill="none" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" style={{ margin: '0 auto 1rem' }}>
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                <polyline points="17 8 12 3 7 8"></polyline>
                <line x1="12" y1="3" x2="12" y2="15"></line>
              </svg>
              {file ? (
                <div>
                  <p style={{ fontWeight: 600, color: 'var(--ink)', fontSize: '1.1rem' }}>{file.name}</p>
                  <p className="unit">Ready to process</p>
                </div>
              ) : (
                <div>
                  <p style={{ fontWeight: 600, color: 'var(--ink)', fontSize: '1.1rem' }}>Drag & drop your CSV file here</p>
                  <p className="unit">or click to browse</p>
                </div>
              )}
            </div>

            <div className="actions" style={{ justifyContent: 'space-between' }}>
              <button 
                className="btn" 
                onClick={(e) => { e.stopPropagation(); handleUpload(); }}
                disabled={!file || isProcessing}
                style={{ minWidth: '160px' }}
              >
                {isProcessing ? 'Processing...' : 'Upload & Process Data'}
              </button>
              
              {status && (
                <div style={{
                  padding: '0.65rem 1rem',
                  borderRadius: 'var(--r-md)',
                  fontSize: '0.9rem',
                  fontWeight: 600,
                  backgroundColor: status.startsWith('Error') ? 'var(--at-risk-wash)' : 'var(--healthy-wash)',
                  color: status.startsWith('Error') ? 'var(--at-risk-text)' : 'var(--healthy-text)',
                  border: `1px solid ${status.startsWith('Error') ? 'var(--at-risk)' : 'var(--healthy)'}`
                }}>
                  {status}
                </div>
              )}
            </div>
          </div>
        </section>

        {results.length > 0 && (
          <section className="panel" style={{ animation: 'lens-grow 0.5s ease' }}>
            <div className="block-head">
              <h2>Processing Results</h2>
            </div>
            <div className="table-wrap" style={{ overflowX: 'auto', marginTop: '1.5rem' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid var(--rule)' }}>
                    <th style={{ padding: '1rem', color: 'var(--muted)', fontWeight: 600, fontSize: '0.9rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Employee Name</th>
                    <th style={{ padding: '1rem', color: 'var(--muted)', fontWeight: 600, fontSize: '0.9rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>PACE Score</th>
                    <th style={{ padding: '1rem', color: 'var(--muted)', fontWeight: 600, fontSize: '0.9rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Calculated Risk Band</th>
                  </tr>
                </thead>
                <tbody>
                  {results.map((r, idx) => (
                    <tr key={idx} style={{ borderBottom: '1px solid var(--rule-soft)' }}>
                      <td style={{ padding: '1rem', fontWeight: 600, color: 'var(--ink)' }}>{r.employee}</td>
                      <td className="num" style={{ padding: '1rem', fontWeight: 700, fontSize: '1.25rem', color: 'var(--ink)' }}>{r.pace}</td>
                      <td style={{ padding: '1rem' }}>
                        <span className={`badge ${r.risk === 'Healthy' ? 'badge-healthy' : r.risk === 'Moderate' ? 'badge-moderate' : 'badge-at-risk'}`}>
                          {r.risk === 'Healthy' && (
                            <svg viewBox="0 0 24 24" width="14" height="14"><path d="M20 6L9 17l-5-5" stroke="currentColor" strokeWidth="2.5" fill="none"/></svg>
                          )}
                          {r.risk}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}
      </div>
    </div>
  );
}
