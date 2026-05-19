import React, { useState, useEffect } from 'react';
import { Eye, EyeOff, Github, GraduationCap } from 'lucide-react';
import * as api from './api';
import './styles.css';

const RETRIEVAL_STRATEGIES = [
  {
    value: "hybrid",
    label: "היברידי",
    description: "משלב בין חיפוש סמנטי לבין חיפוש מילולי מדויק.",
    goodFor: "שאלות כלליות ומורכבות.",
    strengths: "הכי מאוזן, עובד טוב ברוב המקרים.",
    weaknesses: "מורכב יותר לחישוב.",
    examples: ["מי הוליד את אברם?", "מה קרה ביריחו?"]
  },
  {
    value: "dense_only",
    label: "סמנטי בלבד",
    description: "מחפש פסוקים בעלי משמעות דומה באמצעות AI.",
    goodFor: "שאלות רעיוניות וניסוחים חופשיים.",
    strengths: "מבין משמעות כללית, לא דורש מילים מדויקות.",
    weaknesses: "פחות טוב לשמות ומונחים ספציפיים.",
    examples: ["מה התנ״ך אומר על פחד?", "מי הרגיש בודד?"]
  },
  {
    value: "lexical_only",
    label: "מילולי בלבד",
    description: "מחפש התאמות מדויקות של מילים וביטויים.",
    goodFor: "שמות, מונחים מדויקים ופסוקים ספציפיים.",
    strengths: "מדויק מאוד לשמות וביטויים ידועים.",
    weaknesses: "לא מבין משמעות או מילים נרדפות.",
    examples: ["איפה מוזכר שופר?", "איפה כתוב 'נעשה אדם'?"]
  },
  {
    value: "single_verse",
    label: "פסוק בודד",
    description: "מחפש כל פסוק בנפרד, ללא הקשר רחב.",
    goodFor: "ציטוטים מדויקים ושאלות נקודתיות.",
    strengths: "ממוקד מאוד, תוצאות קצרות.",
    weaknesses: "מאבד הקשר של סיפורים ארוכים.",
    examples: ["מה כתוב בפסוק 'ואהבת לרעך כמוך'?", "מי בנה את התיבה?"]
  },
  {
    value: "sliding_window",
    label: "חלון פסוקים",
    description: "מחפש קבוצות של פסוקים יחד לשמירה על הקשר.",
    goodFor: "סיפורים, רצף אירועים ופרשיות.",
    strengths: "שומר על קונטקסט ומבין רצף עלילתי.",
    weaknesses: "עלול להחזיר יותר טקסט מהנדרש.",
    examples: ["מה קרה בעקידת יצחק?", "ספר לי על יציאת מצרים."]
  },
];

const COMPARISON_EXAMPLES = [
  { q: "מי הוליד את אברם?", label: "גנאלוגיה (מילולי vs סמנטי)" },
  { q: "תן לי מקומות שהייתה בהם תקיעת שופר", label: "רשימה (מילולי/היברידי)" },
  { q: "מה התנ״ך אומר על פחד?", label: "נושא רעיוני (סמנטי)" },
];

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
        <p className="subtitle">מערכת שאלות ותשובות מבוססת RAG על התנ״ך</p>

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
              <div style={{ display: 'flex', gap: '15px', alignItems: 'flex-start' }}>
                <div style={{ flex: 1 }}>
                  <label style={{ fontSize: '0.8rem', fontWeight: 'bold', display: 'block', marginBottom: '4px' }}>אסטרטגיית חיפוש:</label>
                  <select
                    value={strategy}
                    onChange={(e) => setStrategy(e.target.value)}
                    className="strategy-select"
                    disabled={loading}
                  >
                    {RETRIEVAL_STRATEGIES.map(s => (
                      <option key={s.value} value={s.value}>{s.label}</option>
                    ))}
                  </select>
                </div>
                <div style={{ flex: 2, fontSize: '0.85rem', borderRight: '2px solid #e2e8f0', paddingRight: '12px' }}>
                  <strong>{selectedStrategyInfo?.description}</strong>
                  <div style={{ marginTop: '4px', color: '#475569' }}>
                    <span style={{ color: '#16a34a' }}>● יתרונות:</span> {selectedStrategyInfo?.strengths}
                  </div>
                  <div style={{ color: '#475569' }}>
                    <span style={{ color: '#dc2626' }}>● חסרונות:</span> {selectedStrategyInfo?.weaknesses}
                  </div>
                </div>
              </div>
            </div>
          )}

          <div className="input-group">
            <input
              type="text"
              placeholder={isCompareMode ? "השוואת אסטרטגיות על השאלה..." : "שאל שאלה על התנ״ך..."}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              disabled={loading}
              autoFocus
              style={{ flex: 1 }}
            />
            <button type="submit" disabled={loading || !question.trim()} style={{ background: isCompareMode ? '#10b981' : '#2563eb' }}>
              {loading ? 'מריץ...' : isCompareMode ? 'השווה' : 'שאל'}
            </button>
          </div>
        </form>
        {error && <div className="error" style={{ marginTop: '1rem' }}>{error}</div>}
      </div>

      {loading && (
        <div className="loading">
          {isCompareMode ? 'מריץ שלוש אסטרטגיות חיפוש במקביל...' : 'מחפש במקורות ומייצר תשובה...'}
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
                      {source.ref}
                      <span className="score-badge-mini">Score: {source.score.toFixed(3)}</span>
                    </div>
                    <div className="source-text-mini">{source.text.slice(0, 150)}...</div>
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
                {source.ref} <span className="ltr">({source.ref_en})</span>
                <div className="scores-container">
                  <span className="score-badge">Final: {source.score.toFixed(3)}</span>
                  {source.dense_score !== undefined && <span className="score-badge semantic">Semantic: {source.dense_score.toFixed(3)}</span>}
                  {source.lexical_score !== undefined && <span className="score-badge lexical">Lexical: {source.lexical_score.toFixed(3)}</span>}
                </div>
              </div>
              <div className="source-text">{source.text}</div>
              <div className="source-meta">Chunk ID: {source.chunk_id} | Type: {source.chunk_type}</div>
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

      <div style={{ marginTop: '3rem', borderTop: '1px solid #e2e8f0', paddingTop: '1.5rem' }}>
        <Footer />
      </div>
    </div>
  );
}


const Footer = () => (
  <footer className="footer rtl">
    <div className="footer-content">
      <p>
        <GraduationCap size={16} style={{ marginLeft: '8px', verticalAlign: 'middle' }} />
        נבנה על ידי <strong>אלעד פיניש</strong> כחלק ממטלה בקורס <strong>AI for Developers</strong>, אוניברסיטת בן-גוריון בנגב.
        <span style={{ marginRight: '10px', opacity: 0.8 }}>(מאי 2026)</span>
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
);
export default App;
