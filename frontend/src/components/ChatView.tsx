import React, { useState, useRef, useEffect } from 'react';
import { Loader2, Send, Presentation, Copy, Check } from 'lucide-react';
import * as api from '../api';
import AgentTrace from './AgentTrace';

// Strip the <b>...</b> highlight tags so copied text is clean.
const stripTags = (t: string) => t.replace(/<\/?b>/g, '');

// Small copy-to-clipboard button shown on each chat bubble.
const CopyButton: React.FC<{ text: string }> = ({ text }) => {
  const [copied, setCopied] = useState(false);
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      const ta = document.createElement('textarea');
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };
  return (
    <button className="copy-btn" onClick={copy} title="העתק" aria-label="העתק">
      {copied ? <Check size={14} /> : <Copy size={14} />}
    </button>
  );
};

interface ChatTurn {
  role: 'user' | 'assistant';
  content: string;
  trace?: api.TraceStep[];
  sources?: string[];
}

// Render an answer that may contain Dicta's <b>...</b> highlights (around the
// number words) as <strong>, without dangerouslySetInnerHTML. Plain answers
// (no <b>) render unchanged.
function renderAnswer(text: string): React.ReactNode {
  return text.split(/(<b>.*?<\/b>)/g).map((part, i) => {
    const m = part.match(/^<b>([\s\S]*?)<\/b>$/);
    return m ? (
      <strong key={i} className="num-match">{m[1]}</strong>
    ) : (
      <React.Fragment key={i}>{part}</React.Fragment>
    );
  });
}

const EXAMPLES = [
  'מה הספר הכי ארוך בתנ״ך?',
  'מי היה אביו של אברהם?',
  'כמה ספרים יש בתנ״ך?',
  'איפה מוזכרת תקיעת שופר?',
];

const ChatView: React.FC = () => {
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [presentationMode, setPresentationMode] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [turns, loading]);

  const send = async (text: string) => {
    const question = text.trim();
    if (!question || loading) return;

    const nextTurns: ChatTurn[] = [...turns, { role: 'user', content: question }];
    setTurns(nextTurns);
    setInput('');
    setLoading(true);
    setError(null);

    try {
      // Send the full conversation history (backend trims to last N).
      const history: api.ChatMessage[] = nextTurns.map((t) => ({ role: t.role, content: t.content }));
      const res = await api.chat(history);
      setTurns([...nextTurns, { role: 'assistant', content: res.answer, trace: res.trace, sources: res.sources }]);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'אירעה שגיאה בעת פניית הסוכן');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    send(input);
  };

  return (
    <div className="chat-view">
      <div className="card">
        <div className="chat-header-row">
          <p className="subtitle" style={{ margin: 0 }}>
            חברותא — סוכן לימוד שבוחר כלים, מחפש, משווה, מתקן את עצמו ומצטט מקורות.
          </p>
          <button
            className={`presentation-toggle ${presentationMode ? 'active' : ''}`}
            onClick={() => setPresentationMode((v) => !v)}
            title="מצב מתאים להצגה מול כיתה"
          >
            <Presentation size={15} style={{ marginLeft: 6, verticalAlign: 'middle' }} />
            {presentationMode ? 'מצב הצגה פעיל' : 'מצב הצגה'}
          </button>
        </div>

        {turns.length === 0 && (
          <div className="examples-row rtl" style={{ marginTop: '1rem' }}>
            <span style={{ fontSize: '0.85rem', color: '#64748b' }}>נסה דוגמה:</span>
            {EXAMPLES.map((q, i) => (
              <button key={i} onClick={() => send(q)} className="example-chip" disabled={loading}>
                {q}
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="chat-thread">
        {turns.map((turn, i) => (
          <div key={i} className={`chat-bubble ${turn.role}`}>
            {turn.role === 'user' ? (
              <div className="chat-user-text">
                <CopyButton text={turn.content} />
                {turn.content}
              </div>
            ) : (
              <>
                {turn.trace && <AgentTrace trace={turn.trace} presentationMode={presentationMode} />}
                <div className="card chat-answer-card">
                  <CopyButton text={stripTags(turn.content)} />
                  <div className="answer-text rtl">{renderAnswer(turn.content)}</div>
                  {turn.sources && turn.sources.length > 0 && (
                    <div className="chat-sources ltr">{turn.sources.slice(0, 6).join(' · ')}</div>
                  )}
                </div>
              </>
            )}
          </div>
        ))}

        {loading && (
          <div className="loading">
            <Loader2 className="spinner" size={28} style={{ marginBottom: '0.75rem' }} />
            <div>הסוכן בוחר כלים ומחפש במקורות...</div>
          </div>
        )}
        <div ref={endRef} />
      </div>

      {error && <div className="error" style={{ marginTop: '1rem' }}>{error}</div>}

      <form onSubmit={handleSubmit} className="chat-input-row">
        <input
          type="text"
          placeholder="שאל את החברותא שאלה על התנ״ך..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={loading}
          autoFocus
        />
        <button type="submit" disabled={loading || !input.trim()}>
          <Send size={16} style={{ marginLeft: 6, verticalAlign: 'middle' }} />
          שלח
        </button>
      </form>
    </div>
  );
};

export default ChatView;
