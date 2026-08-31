import { useState } from 'react';
import './Home.css';

interface Discipline {
  id: string;
  name: string;
  role: string;
  status: 'idle' | 'running' | 'completed' | 'failed';
  statusText: string;
  confidence?: number;
  color: string;
}

interface ChatMessage {
  author: string;
  message: string;
}

interface Blueprints {
  summary: string;
  requirements: string;
  architecture: string;
  database: string;
  api: string;
  testing: string;
  risks: string;
}

// In dev: empty string → Vite proxy forwards /api to localhost:8000
// In Docker/prod: set VITE_BACKEND_URL build arg to point at the backend service
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL ?? '';

export default function Home() {
  const [idea, setIdea] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [coordinatorStatus, setCoordinatorStatus] = useState('Ready to start engineering session.');
  const [activeTab, setActiveTab] = useState<keyof Blueprints>('summary');
  
  const [disciplines, setDisciplines] = useState<Discipline[]>([
    { id: 'coordination', name: 'Engineering Coordinator', role: 'Align session parameters & orchestrate specialists', status: 'idle', statusText: 'Idle', color: '#6366f1' },
    { id: 'requirements', name: 'Requirements Engineering', role: 'Define functional scope & scalability targets', status: 'idle', statusText: 'Idle', color: '#3b82f6' },
    { id: 'architecture', name: 'Architecture Engineering', role: 'Model component structures & topology patterns', status: 'idle', statusText: 'Idle', color: '#10b981' },
    { id: 'database', name: 'Data Engineering', role: 'Design schemas, relations, & validation structures', status: 'idle', statusText: 'Idle', color: '#f59e0b' },
    { id: 'api', name: 'Integration Engineering', role: 'Map REST endpoints & contract payloads', status: 'idle', statusText: 'Idle', color: '#ec4899' },
    { id: 'testing', name: 'Quality Engineering', role: 'Formulate unit, E2E, & performance test specs', status: 'idle', statusText: 'Idle', color: '#8b5cf6' },
    { id: 'risk', name: 'Risk Engineering', role: 'Audit security compliance, load risks, & vulnerabilities', status: 'idle', statusText: 'Idle', color: '#ef4444' },
    { id: 'communication', name: 'Technical Communication', role: 'Package final specification blueprint documents', status: 'idle', statusText: 'Idle', color: '#6b7280' },
  ]);

  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [blueprints, setBlueprints] = useState<Blueprints>({
    summary: '',
    requirements: '',
    architecture: '',
    database: '',
    api: '',
    testing: '',
    risks: ''
  });

  const [readinessScore, setReadinessScore] = useState<number | null>(null);
  const [riskDetails, setRiskDetails] = useState<string>('');
  const [reopeningLoop, setReopeningLoop] = useState(false);
  const [humanApproved, setHumanApproved] = useState<boolean | null>(null);

  const handleApprove = async (approved: boolean) => {
    if (!sessionId) return;
    try {
      await fetch(`${BACKEND_URL}/api/session/approval`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          approved,
          notes: approved ? 'Certified by Lead Systems Architect.' : 'Changes requested by Reviewer.'
        })
      });
      setHumanApproved(approved);
      if (approved) {
        setChatMessages(prev => [
          ...prev,
          {
            author: 'Lead Human Architect',
            message: '✓ Engineering Blueprint approved and certified for production handoff.'
          }
        ]);
      }
    } catch (e) {
      console.error('Failed to submit human approval:', e);
      setHumanApproved(approved);
    }
  };

  const handleDownloadKiroZip = () => {
    if (!sessionId) return;
    const downloadUrl = `${BACKEND_URL}/api/session/${sessionId}/export/kiro/zip`;
    const a = document.createElement('a');
    a.href = downloadUrl;
    a.download = `architectos-kiro-specs-${sessionId.slice(0, 8)}.zip`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  const handleDownloadJson = async () => {
    if (!sessionId) return;
    try {
      const res = await fetch(`${BACKEND_URL}/api/session/${sessionId}/export/kiro`);
      const data = await res.json();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `architectos-blueprint-${sessionId.slice(0, 8)}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (e) {
      console.error('Failed to export JSON blueprint:', e);
    }
  };

  const startSession = async () => {
    if (!idea.trim()) return;
    setIsGenerating(true);
    setReadinessScore(null);
    setRiskDetails('');
    setChatMessages([]);
    setReopeningLoop(false);
    setHumanApproved(null);
    setBlueprints({
      summary: '',
      requirements: '',
      architecture: '',
      database: '',
      api: '',
      testing: '',
      risks: ''
    });

    
    // Reset status
    setDisciplines(prev => prev.map(d => ({ ...d, status: 'idle', statusText: 'Idle', confidence: undefined })));
    setCoordinatorStatus('Initializing collaborative engineering session...');

    try {
      // 1. Start Session
      const startRes = await fetch(`${BACKEND_URL}/api/session/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ idea })
      });
      if (!startRes.ok) throw new Error('Failed to start session on backend.');
      const startData = await startRes.json();
      const currentSessionId = startData.session_id;
      setSessionId(currentSessionId);

      // List of steps to run in order
      const steps = ['coordination', 'requirements', 'architecture', 'database', 'api', 'testing', 'risk'];
      
      let scoreRef: number | null = null;
      let riskDetailsRef = '';

      for (const step of steps) {
        setDisciplines(prev => prev.map(d => d.id === step ? { ...d, status: 'running', statusText: 'Analyzing...' } : d));
        setCoordinatorStatus(`Orchestrating ${step === 'coordination' ? 'Engineering Coordinator' : step + ' specialists'}...`);
        
        // Wait 1.5s per step to make it readable and showcase team collaboration
        await new Promise(r => setTimeout(r, 1500));

        const res = await fetch(`${BACKEND_URL}/api/session/step`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ session_id: currentSessionId, step_id: step, idea })
        });
        
        if (!res.ok) throw new Error(`Step ${step} failed`);
        const stepData = await res.json();
        
        // Update Discipline Status
        setDisciplines(prev => prev.map(d => d.id === step ? { 
          ...d, 
          status: stepData.status === 'failed' ? 'failed' : 'completed', 
          statusText: stepData.status === 'failed' ? 'Review Rejected' : 'Approved / Reviewed',
          confidence: stepData.confidence
        } : d));

        // Add to dialogue
        if (stepData.dialogue) {
          setChatMessages(prev => [...prev, ...stepData.dialogue]);
        }

        // Add to specs
        if (stepData.blueprint_content) {
          setBlueprints(prev => ({
            ...prev,
            [stepData.active_tab]: stepData.blueprint_content
          }));
          setActiveTab(stepData.active_tab as keyof Blueprints);
        }

        if (stepData.readiness_score !== null) {
          scoreRef = stepData.readiness_score;
          setReadinessScore(scoreRef);
        }
        if (stepData.risk_details) {
          riskDetailsRef = stepData.risk_details;
          setRiskDetails(riskDetailsRef);
        }
      }

      // Check if audit score was failed/low (the iterative loop requirement)
      if (scoreRef !== null && scoreRef < 85) {
        // Trigger Reopening Loop Animation
        setReopeningLoop(true);
        setCoordinatorStatus('Engineering Review: Throttling & OAuth2 credentials missing. Reopening Architecture Review...');
        
        // Animate Architecture Engineering reactivating
        setDisciplines(prev => prev.map(d => d.id === 'architecture' ? { ...d, status: 'running', statusText: 'Re-evaluating System Design...' } : d));
        
        await new Promise(r => setTimeout(r, 3000));

        // Rerun Architecture step with retry
        const archRetryRes = await fetch(`${BACKEND_URL}/api/session/step`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ session_id: currentSessionId, step_id: 'architecture_retry', idea })
        });
        if (!archRetryRes.ok) throw new Error('Architecture retry failed');
        const archRetryData = await archRetryRes.json();

        // Update architecture spec
        setDisciplines(prev => prev.map(d => d.id === 'architecture' ? { 
          ...d, 
          status: 'completed', 
          statusText: 'Approved / Reviewed (V2)',
          confidence: archRetryData.confidence 
        } : d));
        if (archRetryData.dialogue) {
          setChatMessages(prev => [...prev, ...archRetryData.dialogue]);
        }
        setBlueprints(prev => ({
          ...prev,
          architecture: archRetryData.blueprint_content
        }));
        setActiveTab('architecture');

        await new Promise(r => setTimeout(r, 2000));

        // Recheck Risk
        setCoordinatorStatus('Risk Engineering: Re-auditing revised architecture design...');
        setDisciplines(prev => prev.map(d => d.id === 'risk' ? { ...d, status: 'running', statusText: 'Re-auditing...' } : d));
        
        await new Promise(r => setTimeout(r, 2000));

        const riskRetryRes = await fetch(`${BACKEND_URL}/api/session/step`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ session_id: currentSessionId, step_id: 'risk_retry', idea })
        });
        if (!riskRetryRes.ok) throw new Error('Risk retry failed');
        const riskRetryData = await riskRetryRes.json();

        setDisciplines(prev => prev.map(d => d.id === 'risk' ? { 
          ...d, 
          status: 'completed', 
          statusText: 'Approved / Reviewed',
          confidence: riskRetryData.confidence 
        } : d));
        if (riskRetryData.dialogue) {
          setChatMessages(prev => [...prev, ...riskRetryData.dialogue]);
        }
        setBlueprints(prev => ({
          ...prev,
          risks: riskRetryData.blueprint_content
        }));
        setReadinessScore(riskRetryData.readiness_score);
        setRiskDetails(riskRetryData.risk_details);
        setActiveTab('risks');

        await new Promise(r => setTimeout(r, 1500));
      }

      // 10. Technical Communication (Finalize Package)
      setDisciplines(prev => prev.map(d => d.id === 'communication' ? { ...d, status: 'running', statusText: 'Assembling blueprint...' } : d));
      setCoordinatorStatus('Technical Communication: Compiling final blueprint documents...');
      await new Promise(r => setTimeout(r, 1500));

      const commRes = await fetch(`${BACKEND_URL}/api/session/step`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: currentSessionId, step_id: 'communication', idea })
      });
      if (!commRes.ok) throw new Error('Communication step failed');
      const commData = await commRes.json();

      setDisciplines(prev => prev.map(d => d.id === 'communication' ? { 
        ...d, 
        status: 'completed', 
        statusText: 'Completed',
        confidence: commData.confidence 
      } : d));
      if (commData.dialogue) {
        setChatMessages(prev => [...prev, ...commData.dialogue]);
      }
      setBlueprints(prev => ({
        ...prev,
        summary: commData.blueprint_content
      }));
      setActiveTab('summary');

      setCoordinatorStatus('Ready for Human Review');
      setIsGenerating(false);

    } catch (err: any) {
      console.error(err);
      setCoordinatorStatus(`Session execution aborted: ${err.message}`);
      setIsGenerating(false);
    }
  };

  return (
    <div className="dashboard-container">
      {/* Top Header */}
      <header className="dashboard-header">
        <div className="brand-badge">ArchitectOS</div>
        <h1 className="main-title">Every Idea. Expertly Engineered.</h1>
        <p className="subtitle">
          A collaborative engineering platform where specialized engineering disciplines work together to plan, review, and continuously improve software specifications.
        </p>
      </header>

      {/* 3-Column Dashboard Layout */}
      <main className="dashboard-grid-3">
        
        {/* Column 1: Input & Workflow Pipeline */}
        <section className="input-section card">
          <h2 className="section-title">Project Idea</h2>
          <div className="textarea-wrapper">
            <textarea
              placeholder="Describe your software idea here... (e.g. 'A real-time whiteboard app with canvas replication and user rooms')"
              value={idea}
              onChange={(e) => setIdea(e.target.value)}
              disabled={isGenerating}
            />
          </div>
          <button 
            className={`generate-btn ${isGenerating ? 'loading' : ''}`} 
            onClick={startSession} 
            disabled={isGenerating || !idea.trim()}
          >
            {isGenerating ? (
              <>
                <span className="spinner"></span>
                Engineering Session in Progress...
              </>
            ) : 'Start Engineering Session'}
          </button>

          {/* Engineering Coordinator Status Bar */}
          <div className="coordinator-status-bar">
            <span className="coord-icon">⚙️</span>
            <span className="coord-text">{coordinatorStatus}</span>
          </div>

          {/* Engineering Workflow */}
          <div className="agent-progress-wrapper">
            <h3 className="section-subtitle">Engineering Workflow</h3>
            <div className="agent-list">
              {disciplines.map((d, index) => (
                <div key={d.id} className={`agent-row ${d.status}`}>
                  <div className="agent-indicator" style={{ backgroundColor: d.color }}>
                    {d.status === 'completed' && '✓'}
                    {d.status === 'failed' && '⚠'}
                    {d.status === 'running' && '●'}
                    {d.status === 'idle' && index + 1}
                  </div>
                  <div className="agent-info">
                    <span className="agent-name">{d.name}</span>
                    <span className="agent-role">{d.role}</span>
                  </div>
                  <div className="agent-meta-status">
                    <span className={`agent-status-badge ${d.status}`}>
                      {d.statusText}
                    </span>
                    {d.confidence && d.status === 'completed' && (
                      <span className="confidence-label">Confidence: {d.confidence}%</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Column 2: New Engineering Conversation Panel */}
        <section className="conversation-section card">
          <h2 className="section-title">Engineering Conversation</h2>
          <div className="conversation-log">
            {chatMessages.length > 0 ? (
              chatMessages.map((msg, index) => (
                <div key={index} className="chat-bubble-container">
                  <div className="chat-header">
                    <span className="chat-avatar-dot"></span>
                    <span className="chat-author">{msg.author}</span>
                  </div>
                  <div className="chat-message">{msg.message}</div>
                </div>
              ))
            ) : (
              <div className="chat-placeholder">
                {isGenerating ? (
                  <div className="chat-loading-spinner-wrapper">
                    <span className="spinner accent"></span>
                    <p>Disciplines aligning on specifications...</p>
                  </div>
                ) : (
                  <>
                    <div className="placeholder-icon">💬</div>
                    <p>Waiting for Engineering Session to start...</p>
                  </>
                )}
              </div>
            )}
          </div>
        </section>

        {/* Column 3: Renamed Output Spec (Engineering Blueprint) */}
        <section className="output-section card">
          <div className="output-header">
            <h2 className="section-title">Engineering Blueprint</h2>
            {readinessScore !== null && (
              <div className="score-badge animate-pop">
                <span className="score-num">{readinessScore}%</span>
                <span className="score-label">Engineering Readiness</span>
              </div>
            )}
          </div>

          {sessionId ? (
            <div className="output-content">
              {/* Tabs with clean names, no extensions */}
              <div className="tab-menu">
                <button className={`tab-btn ${activeTab === 'summary' ? 'active' : ''}`} onClick={() => setActiveTab('summary')}>
                  Executive Summary
                </button>
                <button className={`tab-btn ${activeTab === 'requirements' ? 'active' : ''}`} onClick={() => setActiveTab('requirements')}>
                  Requirements
                </button>
                <button className={`tab-btn ${activeTab === 'architecture' ? 'active' : ''}`} onClick={() => setActiveTab('architecture')}>
                  Architecture
                </button>
                <button className={`tab-btn ${activeTab === 'database' ? 'active' : ''}`} onClick={() => setActiveTab('database')}>
                  Database
                </button>
                <button className={`tab-btn ${activeTab === 'api' ? 'active' : ''}`} onClick={() => setActiveTab('api')}>
                  API
                </button>
                <button className={`tab-btn ${activeTab === 'testing' ? 'active' : ''}`} onClick={() => setActiveTab('testing')}>
                  Tests
                </button>
                <button className={`tab-btn ${activeTab === 'risks' ? 'active' : ''}`} onClick={() => setActiveTab('risks')}>
                  Risk Review
                </button>
              </div>

              {/* Tab Markdown content panels */}
              <div className="tab-panel">
                {blueprints[activeTab] ? (
                  <div className="doc-markdown">
                    {/* Render raw specs pre-formatted */}
                    <div style={{ whiteSpace: 'pre-wrap' }}>{blueprints[activeTab]}</div>
                  </div>
                ) : (
                  <div className="tab-loading">
                    <span className="spinner"></span>
                    <p>Drafting specification sheet...</p>
                  </div>
                )}
              </div>

              {/* Engineering Readiness Details Alert */}
              {riskDetails && (
                <div className={`risk-details-bar ${readinessScore && readinessScore < 85 ? 'warning' : 'success'}`}>
                  <span className="risk-icon">{readinessScore && readinessScore < 85 ? '⚠️' : '🛡️'}</span>
                  <span className="risk-text">{riskDetails}</span>
                </div>
              )}

              {/* Iterative Review Loop UI message */}
              {reopeningLoop && readinessScore && readinessScore < 85 && (
                <div className="iteration-alert animate-pop">
                  <span className="spinner warning-spinner"></span>
                  <span className="alert-text">Engineering Review Throttled. Reopening Architecture module for revision...</span>
                </div>
              )}

              {/* Human Architectural Review & Certification Checkpoint */}
              {!isGenerating && readinessScore !== null && readinessScore >= 85 && (
                <div className="human-approval-card animate-pop">
                  <div className="approval-header">
                    <span className="approval-title">
                      🛡️ Lead Architectural Checkpoint (Ground Rules 04 & 05)
                    </span>
                    {humanApproved === true && (
                      <span className="approval-badge-approved">
                        ✓ Blueprint Certified
                      </span>
                    )}
                  </div>
                  
                  {humanApproved === null ? (
                    <div className="approval-actions">
                      <button className="btn-approve" onClick={() => handleApprove(true)}>
                        ✓ Approve Architecture & Sign Off
                      </button>
                      <button className="btn-reject" onClick={() => handleApprove(false)}>
                        ✕ Request Changes
                      </button>
                    </div>
                  ) : humanApproved === true ? (
                    <p style={{ fontSize: '13px', color: '#6ee7b7' }}>
                      Architecture certified with <strong>{readinessScore}% Verified Blueprint Coverage</strong>. Ready for developer handoff.
                    </p>
                  ) : (
                    <p style={{ fontSize: '13px', color: '#fca5a5' }}>
                      Changes requested. Additional review cycle required.
                    </p>
                  )}
                </div>
              )}

              {/* Export Spec Bundle Controls */}
              {!isGenerating && sessionId && readinessScore !== null && (
                <div className="export-actions-bar animate-pop">
                  <button className="btn-export-kiro" onClick={handleDownloadKiroZip}>
                    📦 Export Spec Bundle (.kiro/specs ZIP)
                  </button>
                  <button className="btn-export-secondary" onClick={handleDownloadJson}>
                    📄 Export JSON Blueprint
                  </button>
                </div>
              )}
            </div>

          ) : (
            <div className="output-placeholder">
              <div className="placeholder-icon">🗂️</div>
              <p>Waiting for Engineering Session...</p>
              <p className="placeholder-sub">The Engineering Coordinator will align specialists to compile document sheets here.</p>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
