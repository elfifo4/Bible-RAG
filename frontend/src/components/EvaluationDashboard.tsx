import React, { useState, useEffect } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import { Activity, SearchCheck, AlertTriangle, Info, Terminal } from 'lucide-react';
import * as api from '../api';

const EvaluationDashboard: React.FC = () => {
  const [summary, setSummary] = useState<api.EvalSummaryResponse | null>(null);
  const [questions, setQuestions] = useState<api.QuestionEvalResult[]>([]);
  const [answers, setAnswers] = useState<api.AnswerEvalResult[]>([]);
  const [ablation, setAblation] = useState<api.AblationResults | null>(null);
  const [errors, setErrors] = useState<api.ErrorAnalysisResults | null>(null);
  const [selectedStrategy, setSelectedStrategy] = useState('hybrid');
  const [filter, setFilter] = useState<'all' | 'success' | 'failure'>('all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    fetchQuestions(selectedStrategy);
    fetchAnswers(selectedStrategy);
  }, [selectedStrategy]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const summaryData = await api.getEvalSummary();
      setSummary(summaryData);

      const ablationData = await api.getEvalAblation();
      setAblation(ablationData);

      const errorData = await api.getEvalErrors();
      setErrors(errorData);

      await fetchQuestions('hybrid');
      await fetchAnswers('hybrid');
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

  const fetchAnswers = async (strat: string) => {
    try {
      const answersData = await api.getEvalAnswers(strat);
      setAnswers(answersData.results);
    } catch (err) {
      console.error('Error fetching answers:', err);
      setAnswers([]);
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
      {summary.metadata && (
        <div style={{ fontSize: '0.8rem', color: '#64748b', marginBottom: '1rem', textAlign: 'left' }} className="ltr">
          Last Evaluation Run: {summary.metadata.last_run} | Questions: {summary.metadata.total_questions}
        </div>
      )}
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

      {/* 4. Answer Quality Section */}
      <div className="card">
        <h3>בדיקת איכות תשובות (LLM Generation)</h3>
        {answers.length > 0 ? (
          <>
            <div className="metrics-grid" style={{ marginTop: '1rem' }}>
              <div className="card metric-card">
                <div className="metric-label">תשובות שנבדקו</div>
                <div className="metric-value">{answers.length}</div>
              </div>
              <div className="card metric-card">
                <div className="metric-label">מכיל תשובת ייחוס</div>
                <div className="metric-value">
                  {((answers.filter(a => a.contains_reference_answer).length / answers.length) * 100).toFixed(0)}%
                </div>
              </div>
              <div className="card metric-card">
                <div className="metric-label">כולל מקורות</div>
                <div className="metric-value">
                  {((answers.filter(a => a.has_sources).length / answers.length) * 100).toFixed(0)}%
                </div>
              </div>
            </div>

            <div className="eval-table-container">
              <table className="eval-table">
                <thead>
                  <tr>
                    <th>שאלה</th>
                    <th>תשובת ייחוס</th>
                    <th>תשובה שנוצרה</th>
                    <th>מקורות</th>
                  </tr>
                </thead>
                <tbody>
                  {answers.map((a, i) => (
                    <tr key={i}>
                      <td>{a.question}</td>
                      <td>{a.reference_answer}</td>
                      <td style={{ fontSize: '0.8rem' }}>{a.generated_answer}</td>
                      <td style={{ fontSize: '0.7rem' }}>{a.sources.join(', ')}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '1rem' }}>
              <Info size={14} style={{ verticalAlign: 'middle', marginLeft: '4px' }} />
              ניתן למלא הערכה ידנית מעמיקה בקובץ: <code className="ltr">eval/results/manual_eval_template.csv</code>
            </p>
          </>
        ) : (
          <div style={{ padding: '2rem', textAlign: 'center', color: '#94a3b8' }}>
            עדיין לא הורצה הערכת תשובות. הרץ:
            <code className="ltr" style={{ display: 'block', marginTop: '0.5rem' }}>
              python3 eval/run_eval.py --strategy {selectedStrategy} --include-generation --limit 10
            </code>
          </div>
        )}
      </div>

      {/* 5. Ablation Section */}
      <div className="card">
        <h3>ניסויי Ablation (רכיבים מנוטרלים)</h3>
        {ablation?.available ? (
          <div className="ablation-container">
            <p style={{ fontSize: '0.85rem', color: '#64748b' }}>
              מציג את ההשפעה של שינוי פרמטרים בודדים על ביצועי המערכת.
            </p>

            <h4 style={{ marginTop: '1.5rem' }}>השפעת אסטרטגיית ה-Retrieval (Top-K=5)</h4>
            <div className="eval-table-container">
              <table className="eval-table">
                <thead>
                  <tr>
                    <th>אסטרטגיה</th>
                    <th>Hit@1</th>
                    <th>Hit@3</th>
                    <th>Hit@5</th>
                    <th>MRR</th>
                  </tr>
                </thead>
                <tbody>
                  {ablation.results?.retrieval_strategy_ablation.map((r, i) => (
                    <tr key={i}>
                      <td>{r.variant}</td>
                      <td>{(r.hit_at_1 * 100).toFixed(1)}%</td>
                      <td>{(r.hit_at_3 * 100).toFixed(1)}%</td>
                      <td>{(r.hit_at_5 * 100).toFixed(1)}%</td>
                      <td>{r.mrr.toFixed(3)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <h4 style={{ marginTop: '2rem' }}>השפעת Top-K (אסטרטגיה: Hybrid)</h4>
            <div className="eval-table-container">
              <table className="eval-table">
                <thead>
                  <tr>
                    <th>K</th>
                    <th>Hit@1</th>
                    <th>Hit@3</th>
                    <th>Hit@5</th>
                    <th>MRR</th>
                  </tr>
                </thead>
                <tbody>
                  {ablation.results?.top_k_ablation.map((r, i) => (
                    <tr key={i}>
                      <td>{r.top_k}</td>
                      <td>{(r.hit_at_1 * 100).toFixed(1)}%</td>
                      <td>{(r.hit_at_3 * 100).toFixed(1)}%</td>
                      <td>{r.hit_at_5 ? (r.hit_at_5 * 100).toFixed(1) + '%' : (r.top_k < 5 ? '-' : (r.hit_at_5 * 100).toFixed(1) + '%')}</td>
                      <td>{r.mrr.toFixed(3)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          <div style={{ padding: '2rem', textAlign: 'center', color: '#94a3b8' }}>
            עדיין לא הורצו ניסויי ablation במערכת. הרץ:
            <code className="ltr" style={{ display: 'block', marginTop: '0.5rem' }}>
              python3 eval/run_eval.py --ablation
            </code>
          </div>
        )}
      </div>

      {/* 6. Error Analysis Section */}
      <div className="card">
        <h3>ניתוח שגיאות (Error Analysis)</h3>
        {errors?.available ? (
          <div>
            <div className="metrics-grid">
              <div className="card metric-card">
                <div className="metric-label">סך כישלונות</div>
                <div className="metric-value" style={{ color: '#dc2626' }}>{errors.results?.summary.total_failures}</div>
              </div>
            </div>

            <h4 style={{ marginTop: '1.5rem' }}>התפלגות סוגי שגיאות</h4>
            <div className="eval-table-container">
              <table className="eval-table">
                <thead>
                  <tr>
                    <th>סוג שגיאה</th>
                    <th>מספר מקרים</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(errors.results?.summary.by_category || {}).map(([cat, count]) => (
                    <tr key={cat}>
                      <td>{cat}</td>
                      <td>{count as number}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <h4 style={{ marginTop: '2rem' }}>דוגמאות לכישלונות מייצגים</h4>
            <div className="eval-table-container">
              <table className="eval-table">
                <thead>
                  <tr>
                    <th>שאלה</th>
                    <th>סוג שגיאה</th>
                    <th>הסבר</th>
                    <th>הצעת שיפור</th>
                  </tr>
                </thead>
                <tbody>
                  {errors.results?.failures.slice(0, 10).map((f, i) => (
                    <tr key={i}>
                      <td>{f.question}</td>
                      <td style={{ fontSize: '0.8rem', fontWeight: 'bold' }}>{f.category}</td>
                      <td style={{ fontSize: '0.8rem' }}>{f.reason}</td>
                      <td style={{ fontSize: '0.8rem', color: '#16a34a' }}>{f.suggested_fix}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          <div style={{ padding: '2rem', textAlign: 'center', color: '#94a3b8' }}>
            עדיין לא נוצר ניתוח שגיאות. הרץ:
            <code className="ltr" style={{ display: 'block', marginTop: '0.5rem' }}>
              python3 eval/error_analysis.py
            </code>
          </div>
        )}
      </div>
    </div>
  );
};

export default EvaluationDashboard;
