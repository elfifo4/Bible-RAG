import React, { useState, useEffect } from 'react';
import { Eye, EyeOff, Github, GraduationCap, X, Loader2 } from 'lucide-react';
import * as api from './api';
import { RETRIEVAL_STRATEGIES, COMPARISON_EXAMPLES } from './constants';
import './styles.css';

function App() {
  const [isAuth, setIsAuth] = useState(api.isAuthenticated());
  const [password, setPassword] = useState('');
  const [question, setQuestion] = useState('');
  const [strategy, setStrategy] = useState('hybrid');
  const [isCompareMode, setIsCompareMode] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<api.AskResponse | null>(null);
  const [compareResult, setCompareResult] = useState<api.CompareResponse | null>(null);
  const [showDebug, setShowDebug] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const selectedStrategyInfo = RETRIEVAL_STRATEGIES.find(s => s.value === strategy);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.login(password);
      setIsAuth(true);
      setError(null);
    } catch (err: any) {
      setError('סיסמה לא נכונה');
    }
  };

  const handleAsk = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;

    setLoading(true);
    setError(null);
    setResult(null);
    setCompareResult(null);

    try {
      if (isCompareMode) {
        const data = await api.compare(question);
        setCompareResult(data);
      } else {
        const data = await api.ask(question, 5, true, strategy);
        setResult(data);
      }
    } catch (err: any) {
      if (err.response?.status === 401) {
        setIsAuth(false);
        api.logout();
      }
      setError(err.response?.data?.detail || 'אירעה שגיאה בביצוע השאילתה');
    } finally {
      setLoading(false);
    }
  };

  const handleExampleClick = (q: string) => {
    setQuestion(q);
  };

  const handleLogout = () => {
    api.logout();
    setIsAuth(false);
    setResult(null);
  };

  if (!isAuth) {
    return (
      <div className="container rtl">
        <div className="card">
          <h1 className="title">תנ״ך RAG</h1>
          <p className="subtitle">יש להזין סיסמה</p>
          <form onSubmit={handleLogin} className="login-form">
            <div className="password-container">
              <input
                type={showPassword ? "text" : "password"}
                placeholder="סיסמה"
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  if (error) setError(null);
                }}
                className="password-input"
                autoFocus
              />
              <button
                type="button"
                className="password-toggle"
                onClick={() => setShowPassword(!showPassword)}
                aria-label={showPassword ? "הסתר סיסמה" : "הצג סיסמה"}
              >
                {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
              </button>
            </div>
            <button type="submit" className="login-button">כניסה</button>
          </form>
          {error && <div className="error mt-4">{error}</div>}
        </div>

        <Footer />
      </div>
    );
  }

  return (
    <div className="container rtl">
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h1 className="title">תנ״ך RAG</h1>
          <div style={{ display: 'flex', gap: '10px' }}>
            <button
              onClick={() => setIsCompareMode(!isCompareMode)}
              style={{ background: isCompareMode ? '#10b981' : '#94a3b8', fontSize: '0.85rem' }}
            >
              {isCompareMode ? 'מצב השוואה פעיל' : 'הפעל מצב השוואה'}
            </button>
            <button onClick={handleLogout} style={{ background: '#64748b', fontSize: '0.85rem' }}>התנתק</button>
          </div>
        </div>
        <p className="subtitle">
          מערכת שאלות ותשובות מבוססת{' '}
          <a
            href="https://en.wikipedia.org/wiki/Retrieval-augmented_generation"
            target="_blank"
            rel="noopener noreferrer"
            className="rag-link"
          >
            RAG
          </a>{' '}
          על התנ״ך
        </p>
        <div className="examples-row rtl">
          <span style={{ fontSize: '0.85rem', color: '#64748b' }}>נסה דוגמה:</span>
          {COMPARISON_EXAMPLES.map((ex, i) => (
            <button
              key={i}
              onClick={() => handleExampleClick(ex.q)}
              className="example-chip"
            >
              {ex.label}
            </button>
          ))}
        </div>

        <form onSubmit={handleAsk} className="input-group-vertical">
          {!isCompareMode && (
            <div className="strategy-info-box rtl">
              <label style={{ fontSize: '0.8rem', fontWeight: 'bold', display: 'block', marginBottom: '12px' }}>אסטרטגיית חיפוש:</label>
              <div className="strategy-radio-group-horizontal">
                {RETRIEVAL_STRATEGIES.map(s => (
                  <label key={s.value} className={`strategy-radio-label ${strategy === s.value ? 'active' : ''}`}>
                    <input
                      type="radio"
                      name="strategy"
                      value={s.value}
                      checked={strategy === s.value}
                      onChange={(e) => setStrategy(e.target.value)}
                      disabled={loading}
                    />
                    {s.label}
                  </label>
                ))}
              </div>

              <div className="strategy-description-bottom">
                <strong>{selectedStrategyInfo?.description}</strong>
                <div className="strategy-pro-con">
                  <div style={{ color: '#475569' }}>
                    <span style={{ color: '#16a34a', fontWeight: 'bold' }}>● יתרונות:</span> {selectedStrategyInfo?.strengths}
                  </div>
                  <div style={{ color: '#475569' }}>
                    <span style={{ color: '#dc2626', fontWeight: 'bold' }}>● חסרונות:</span> {selectedStrategyInfo?.weaknesses}
                  </div>
                </div>
              </div>
            </div>
          )}

          <div className="input-group">
            <div style={{ position: 'relative', flex: 1, display: 'flex' }}>
              <input
                type="text"
                placeholder={isCompareMode ? "השוואת אסטרטגיות על השאלה..." : "שאל שאלה על התנ״ך..."}
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                disabled={loading}
                autoFocus
                style={{ width: '100%', paddingLeft: question ? '2.5rem' : '1rem' }}
              />
              {question && !loading && (
                <button
                  type="button"
                  onClick={() => setQuestion('')}
                  className="clear-button"
                  title="נקה שאלה"
                >
                  <X size={18} />
                </button>
              )}
            </div>
            <button type="submit" disabled={loading || !question.trim()} style={{ background: isCompareMode ? '#10b981' : '#2563eb' }}>
              {loading ? 'מריץ...' : isCompareMode ? 'השווה' : 'שאל'}
            </button>
          </div>
        </form>
        {error && <div className="error" style={{ marginTop: '1rem' }}>{error}</div>}
      </div>

      {loading && (
        <div className="loading">
          <Loader2 className="spinner" size={32} style={{ marginBottom: '1rem' }} />
          <div>
            {isCompareMode ? 'מריץ שלוש אסטרטגיות חיפוש במקביל...' : 'מחפש במקורות ומייצר תשובה...'}
          </div>
        </div>
      )}

      {compareResult && (
        <div className="compare-grid rtl">
          {Object.entries(compareResult.results).map(([stratKey, stratRes]) => {
            const info = RETRIEVAL_STRATEGIES.find(s => s.value === stratKey);
            return (
              <div key={stratKey} className="compare-column">
                <div className="compare-header">
                  <h3>{info?.label}</h3>
                  <div style={{ fontSize: '0.75rem', opacity: 0.8 }}>{info?.description}</div>
                </div>

                <div className="card" style={{ padding: '1rem', borderTop: '4px solid #3b82f6' }}>
                  <h4 style={{ margin: '0 0 10px 0' }}>תשובה</h4>
                  <div className="answer-text" style={{ fontSize: '0.95rem' }}>{stratRes.answer}</div>
                </div>

                <h4 style={{ marginBottom: '10px' }}>מקורות מובילים:</h4>
                {stratRes.context.slice(0, 3).map((source, idx) => (
                  <div key={idx} className="card source-card-mini">
                    <div className="source-ref-mini">
                      {source.metadata.ref}
                      <span className="score-badge-mini">Score: {source.score.toFixed(3)}</span>
                    </div>
                    <div className="source-text-mini">{source.display_text.slice(0, 150)}...</div>
                  </div>
                ))}
              </div>
            );
          })}
        </div>
      )}

      {result && !isCompareMode && (
        <>
          <div className="card">
            <h2 className="rtl">תשובה</h2>
            <div className="answer-text rtl">{result.answer}</div>
          </div>

          <h3 className="rtl">מקורות שצוטטו</h3>
          {result.context.map((source, idx) => (
            <div key={idx} className="card source-card rtl">
              <div className="source-ref">
                {source.metadata.ref} <span className="ltr">({source.metadata.ref_en})</span>
                <div className="scores-container">
                  <span className="score-badge">Final: {source.score.toFixed(3)}</span>
                  {source.dense_score !== undefined && <span className="score-badge semantic">Semantic: {source.dense_score.toFixed(3)}</span>}
                  {source.lexical_score !== undefined && <span className="score-badge lexical">Lexical: {source.lexical_score.toFixed(3)}</span>}
                </div>
              </div>
              <div className="source-text">{source.display_text}</div>
              <div className="source-meta">Chunk ID: {source.chunk_id} | Type: {source.metadata.chunk_type}</div>
            </div>
          ))}

          <button
            onClick={() => setShowDebug(!showDebug)}
            style={{ background: '#94a3b8', marginTop: '1rem' }}
          >
            {showDebug ? 'הסתר מידע טכני' : 'הצג מידע טכני'}
          </button>

          <div className={`debug-panel ltr ${showDebug && result.debug ? 'visible' : ''}`}>
            {result.debug && (
              <>
                <pre>{JSON.stringify(result.debug, null, 2)}</pre>
                <pre>Question: {result.question}</pre>
              </>
            )}
          </div>
        </>
      )}

      <div style={{ marginTop: '3rem', borderTop: '1px solid #e2e8f0', paddingTop: '1.5rem' }}>
        <Footer />
      </div>
    </div>
  );
}


const Footer = () => (
  <footer className="footer rtl">
    <div className="footer-content">
      <div className="footer-text-lines">
        <p>
          <GraduationCap size={16} style={{ marginLeft: '8px', verticalAlign: 'middle' }} />
          נבנה על ידי{' '}
          <a
            href="https://www.linkedin.com/in/elad-finish/"
            target="_blank"
            rel="noopener noreferrer"
            className="linkedin-link"
          >
            <strong>אלעד פיניש</strong>
          </a>{' '}
          כחלק ממטלת אמצע בקורס <strong>AI for Developers</strong>
        </p>
        <p>מטעם המכון לבינה מלאכותית The Institute</p>
        <p>אוניברסיטת בן-גוריון בנגב (מאי 2026)</p>
      </div>

      <a
        href="https://github.com/elfifo4/Bible-RAG"
        target="_blank"
        rel="noopener noreferrer"
        className="github-link"
      >
        <Github size={16} style={{ marginLeft: '6px' }} />
        צפייה בקוד המקור ב-GitHub
      </a>
    </div>
  </footer>
);
export default App;
