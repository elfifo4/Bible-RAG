import React, { useState, useEffect } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import { Activity, SearchCheck, AlertTriangle, Info, Terminal } from 'lucide-react';
import * as api from '../api';

const EvaluationDashboard: React.FC = () => {
  const [summary, setSummary] = useState<api.EvalSummaryResponse | null>(null);
  const [questions, setQuestions] = useState<api.QuestionEvalResult[]>([]);
  const [selectedStrategy, setSelectedStrategy] = useState('hybrid');
  const [filter, setFilter] = useState<'all' | 'success' | 'failure'>('all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    fetchQuestions(selectedStrategy);
  }, [selectedStrategy]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const summaryData = await api.getEvalSummary();
      setSummary(summaryData);
      await fetchQuestions('hybrid');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'אירעה שגיאה בטעינת נתוני ההערכה');
    } finally {
      setLoading(false);
    }
  };

  const fetchQuestions = async (strat: string) => {
    try {
      const questionsData = await api.getEvalQuestions(strat);
      setQuestions(questionsData.results);
    } catch (err) {
      console.error('Error fetching questions:', err);
    }
  };

  if (loading) return <div className="loading">טוען נתוני הערכה...</div>;

  if (error || !summary) {
    return (
      <div className="card rtl">
        <div className="error">
          <AlertTriangle size={24} style={{ marginLeft: '10px' }} />
          <div>{error}</div>
        </div>
        <div style={{ marginTop: '1.5rem' }}>
          <p>נראה שעדיין לא הורצה הערכה. כדי לראות נתונים כאן, עליך להריץ את הפקודה הבאה בטרמינל:</p>
          <div className="debug-panel ltr" style={{ opacity: 1, maxHeight: 'none', padding: '1rem' }}>
            <Terminal size={16} style={{ marginRight: '8px' }} />
            python3 eval/run_eval.py --strategy all
          </div>
          <button onClick={fetchData} style={{ marginTop: '1rem' }}>נסה שוב</button>
        </div>
      </div>
    );
  }

  const chartData = Object.values(summary.strategies).map(s => ({
    name: s.strategy === 'hybrid' ? 'היברידי' : s.strategy === 'dense_only' ? 'סמנטי' : 'מילולי',
    'Hit@1': s.hit_at_1,
    'Hit@3': s.hit_at_3,
    'Hit@5': s.hit_at_5,
    'MRR': s.mrr
  }));

  const filteredQuestions = questions.filter(q => {
    if (filter === 'success') return q.hit_at_5;
    if (filter === 'failure') return !q.hit_at_5;
    return true;
  });

  const metrics = summary.strategies[selectedStrategy] || Object.values(summary.strategies)[0];

  return (
    <div className="rtl">
      {/* 1. Metrics Cards */}
      <div className="metrics-grid">
        <div className="card metric-card">
          <div className="metric-label">דיוק מקום ראשון (Hit@1)</div>
          <div className="metric-value">{(metrics.hit_at_1 * 100).toFixed(1)}%</div>
        </div>
        <div className="card metric-card">
          <div className="metric-label">דיוק עד 3 (Hit@3)</div>
          <div className="metric-value">{(metrics.hit_at_3 * 100).toFixed(1)}%</div>
        </div>
        <div className="card metric-card">
          <div className="metric-label">דיוק עד 5 (Hit@5)</div>
          <div className="metric-value">{(metrics.hit_at_5 * 100).toFixed(1)}%</div>
        </div>
        <div className="card metric-card">
          <div className="metric-label">Recall@5</div>
          <div className="metric-value">{(metrics.recall_at_5 * 100).toFixed(1)}%</div>
        </div>
        <div className="card metric-card">
          <div className="metric-label">איכות דירוג (MRR)</div>
          <div className="metric-value">{metrics.mrr.toFixed(3)}</div>
        </div>
      </div>

      {/* 2. Charts */}
      <div className="card">
        <h3>השוואת אסטרטגיות חיפוש</h3>
        <div style={{ width: '100%', height: 300 }}>
          <ResponsiveContainer>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis domain={[0, 1]} />
              <Tooltip />
              <Legend />
              <Bar dataKey="Hit@1" fill="#3b82f6" />
              <Bar dataKey="Hit@3" fill="#60a5fa" />
              <Bar dataKey="Hit@5" fill="#93c5fd" />
              <Bar dataKey="MRR" fill="#10b981" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* 3. Detailed Inspector */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <h3>פירוט שאילתות</h3>
          <div style={{ display: 'flex', gap: '10px' }}>
            <select
              value={selectedStrategy}
              onChange={(e) => setSelectedStrategy(e.target.value)}
              className="strategy-select-mini"
            >
              {Object.keys(summary.strategies).map(s => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value as any)}
              className="strategy-select-mini"
            >
              <option value="all">כל השאלות</option>
              <option value="success">הצלחות בלבד</option>
              <option value="failure">כשלונות בלבד</option>
            </select>
          </div>
        </div>

        <div className="eval-table-container">
          <table className="eval-table">
            <thead>
              <tr>
                <th>שאלה</th>
                <th>Hit@5</th>
                <th>דירוג ראשון</th>
                <th>מקורות שאוחזרו</th>
              </tr>
            </thead>
            <tbody>
              {filteredQuestions.map((q, i) => (
                <tr key={i} className={q.hit_at_5 ? 'row-success' : 'row-failure'}>
                  <td>{q.question}</td>
                  <td style={{ textAlign: 'center' }}>
                    {q.hit_at_5 ? <SearchCheck className="text-success" /> : <AlertTriangle className="text-failure" />}
                  </td>
                  <td style={{ textAlign: 'center' }}>{q.first_relevant_rank || '-'}</td>
                  <td className="ltr" style={{ fontSize: '0.75rem' }}>
                    {q.retrieved_refs.slice(0, 3).join(', ')}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* 4. Ablation Section (Placeholder for now) */}
      <div className="card">
        <h3>ניסויי Ablation (רכיבים מנוטרלים)</h3>
        <p style={{ fontSize: '0.85rem', color: '#64748b' }}>
          בחלק זה ניתן לראות את ההשפעה של שינוי פרמטרים בודדים על ביצועי המערכת (למשל: גודל חלון, Top-K, סוג מודל).
        </p>
        <div style={{ padding: '2rem', textAlign: 'center', border: '2px dashed #e2e8f0', borderRadius: '0.5rem', color: '#94a3b8' }}>
          עדיין לא הורצו ניסויי ablation במערכת.
        </div>
      </div>
    </div>
  );
};

export default EvaluationDashboard;
