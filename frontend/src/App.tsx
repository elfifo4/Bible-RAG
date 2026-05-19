import React, { useState, useEffect } from 'react';
import { Eye, EyeOff, Github, GraduationCap } from 'lucide-react';
import * as api from './api';
import './styles.css';

function App() {
  const [isAuth, setIsAuth] = useState(api.isAuthenticated());
  const [password, setPassword] = useState('');
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<api.AskResponse | null>(null);
  const [showDebug, setShowDebug] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

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
    try {
      const data = await api.ask(question);
      setResult(data);
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
                onChange={(e) => setPassword(e.target.value)}
                className="password-input"
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

        <footer className="footer rtl">
          <div className="footer-content">
            <p>
              <GraduationCap size={16} style={{ marginLeft: '8px', verticalAlign: 'middle' }} />
              נבנה על ידי <strong>אלעד פיניש</strong> כחלק ממטלה בקורס <strong>AI for Developers</strong>, אוניברסיטת בן-גוריון בנגב.
            </p>
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
      </div>
    );
  }

  return (
    <div className="container rtl">
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h1 className="title">תנ״ך RAG</h1>
          <button onClick={handleLogout} style={{ background: '#64748b' }}>התנתק</button>
        </div>
        <p className="subtitle">מערכת שאלות ותשובות מבוססת RAG על התנ״ך</p>

        <form onSubmit={handleAsk} className="input-group">
          <input
            type="text"
            placeholder="שאל שאלה על התנ״ך..."
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            disabled={loading}
          />
          <button type="submit" disabled={loading || !question.trim()}>
            {loading ? 'חושב...' : 'שאל'}
          </button>
        </form>
        {error && <div className="error" style={{ marginTop: '1rem' }}>{error}</div>}
      </div>

      {loading && <div className="loading">מחפש במקורות ומייצר תשובה...</div>}

      {result && (
        <>
          <div className="card">
            <h2 className="rtl">תשובה</h2>
            <div className="answer-text rtl">{result.answer}</div>
          </div>

          <h3 className="rtl">מקורות שצוטטו</h3>
          {result.context.map((source, idx) => (
            <div key={idx} className="card source-card rtl">
              <div className="source-ref">
                {source.ref} <span className="ltr">({source.ref_en})</span>
                <span className="score-badge">Score: {source.score.toFixed(4)}</span>
              </div>
              <div className="source-text">{source.text}</div>
            </div>
          ))}

          <button
            onClick={() => setShowDebug(!showDebug)}
            style={{ background: '#94a3b8', marginTop: '1rem' }}
          >
            {showDebug ? 'הסתר מידע טכני' : 'הצג מידע טכני'}
          </button>

          {showDebug && result.debug && (
            <div className="debug-panel ltr">
              <pre>{JSON.stringify(result.debug, null, 2)}</pre>
              <pre>Question: {result.question}</pre>
            </div>
          )}
        </>
      )}

      <footer className="footer rtl" style={{ marginTop: '3rem', borderTop: '1px solid #e2e8f0', paddingTop: '1.5rem' }}>
        <div className="footer-content">
          <p>
            <GraduationCap size={16} style={{ marginLeft: '8px', verticalAlign: 'middle' }} />
            נבנה על ידי <strong>אלעד פיניש</strong> כחלק ממטלה בקורס <strong>AI for Developers</strong>, אוניברסיטת בן-גוריון בנגב.
          </p>
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
    </div>
  );
}

export default App;
