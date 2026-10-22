import React, { useState } from 'react';
import { Link } from 'react-router-dom';

export default function UploadModal({
  onClose,
  onSuccess
}: {
  onClose: () => void;
  onSuccess: (results: any[]) => void;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<string>('');
  const [isDragging, setIsDragging] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  const [isSuccess, setIsSuccess] = useState(false);

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

      const results = await response.json();
      setStatus('Success! Processing complete.');
      onSuccess(results.data);
      setIsSuccess(true);
    } catch (error: any) {
      setStatus(`Error: ${error.message}`);
      setIsProcessing(false);
    }
  };

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
      backgroundColor: 'rgba(0,0,0,0.5)', zIndex: 100,
      display: 'flex', alignItems: 'center', justifyContent: 'center'
    }}>
      <div className="panel" style={{ width: '100%', maxWidth: '600px', margin: '2rem', position: 'relative' }}>
        <button onClick={onClose} style={{ position: 'absolute', top: '1rem', right: '1rem', background: 'none', border: 'none', fontSize: '1.5rem', cursor: 'pointer', color: 'var(--muted)' }}>&times;</button>
        
        {isSuccess ? (
          <div style={{ textAlign: 'center', padding: '2rem 1rem' }}>
            <svg viewBox="0 0 24 24" width="64" height="64" stroke="var(--healthy)" fill="none" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ margin: '0 auto 1.5rem' }}>
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
              <polyline points="22 4 12 14.01 9 11.01"></polyline>
            </svg>
            <h2 style={{ marginBottom: '1rem' }}>Data Successfully Processed!</h2>
            <p className="muted" style={{ marginBottom: '2rem' }}>Your organization data has been calculated and is ready to view.</p>
            <Link to="/dashboard" onClick={onClose} className="btn" style={{ textDecoration: 'none', display: 'inline-block' }}>
              View Dashboard
            </Link>
          </div>
        ) : (
          <>
            <div className="block-head">
              <h2>Upload Work Metadata (CSV)</h2>
            </div>
            <p className="muted" style={{ marginBottom: '1.5rem' }}>
              Ensure your dataset includes <code>meeting_load</code>, <code>focus_gap</code>, and <code>completion_rate</code> columns.
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
          </>
        )}
      </div>
    </div>
  );
}
