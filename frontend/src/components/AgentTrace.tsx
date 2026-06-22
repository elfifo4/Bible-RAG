import React, { useState } from 'react';
import { TraceStep } from '../api';

// Hebrew explanations for each tool, surfaced in the trace cards.
const TOOL_INFO: Record<string, { icon: string; desc: string }> = {
  search_tanakh: { icon: '🔍', desc: 'חיפוש סמנטי/מילולי/היברידי בתוך פסוקי התנ״ך' },
  lookup_reference: { icon: '📖', desc: 'שליפה מדויקת לפי ספר, פרק ופסוק' },
  bible_structure: { icon: '📚', desc: 'תשובות לשאלות מבניות על ספרי התנ״ך, מספר פרקים וסדר הספרים' },
  compare_retrieval_strategies: { icon: '⚖️', desc: 'השוואה בין dense, lexical ו-hybrid כדי להבין איזו אסטרטגיה מתאימה' },
  search_number: { icon: '🔢', desc: 'חיפוש מספר (בכתיב מילולי) בפסוקי התנ״ך דרך מנוע החיפוש של Dicta' },
};

const CONFIDENCE_LABEL: Record<string, string> = {
  high: 'ביטחון גבוה',
  medium: 'ביטחון בינוני',
  low: 'ביטחון נמוך',
};

function stepIcon(step: TraceStep): string {
  if (step.type === 'final_answer') return '✅';
  if (step.type === 'fallback') return '⚠️';
  if (step.tool && TOOL_INFO[step.tool]) return TOOL_INFO[step.tool].icon;
  return '•';
}

function formatArgs(args: Record<string, any> | null): string {
  if (!args || Object.keys(args).length === 0) return '';
  return Object.entries(args)
    .map(([k, v]) => `${k}: ${typeof v === 'string' ? v : JSON.stringify(v)}`)
    .join(' · ');
}

interface Props {
  trace: TraceStep[];
  presentationMode: boolean;
}

const AgentTrace: React.FC<Props> = ({ trace, presentationMode }) => {
  // In presentation mode the trace is open by default and stays expanded.
  const [open, setOpen] = useState(presentationMode);

  React.useEffect(() => {
    setOpen(presentationMode);
  }, [presentationMode]);

  if (!trace || trace.length === 0) return null;

  const toolSteps = trace.filter((s) => s.type === 'tool_call').length;

  return (
    <div className={`agent-trace ${presentationMode ? 'presentation' : ''}`}>
      {!presentationMode && (
        <button className="trace-toggle" onClick={() => setOpen(!open)}>
          {open
            ? 'הסתר את צעדי הסוכן'
            : `הצג את צעדי הסוכן (${toolSteps === 1 ? 'כלי אחד' : `${toolSteps} כלים`})`}
        </button>
      )}

      {open && (
        <div className="trace-timeline">
          {trace.map((step, i) => (
            <div key={step.step} className={`trace-step conf-${step.confidence} type-${step.type}`}>
              <div className="trace-marker">
                <span className="trace-icon">{stepIcon(step)}</span>
                {i < trace.length - 1 && <span className="trace-line" />}
              </div>
              <div className="trace-card">
                <div className="trace-card-head">
                  <span className="trace-step-num">צעד {step.step}</span>
                  <span className="trace-label">{step.label}</span>
                  <span className={`trace-conf conf-badge-${step.confidence}`}>
                    {CONFIDENCE_LABEL[step.confidence]}
                  </span>
                </div>

                {step.tool && TOOL_INFO[step.tool] && (
                  <div className="trace-tool-desc">{TOOL_INFO[step.tool].desc}</div>
                )}

                {!presentationMode && step.args && Object.keys(step.args).length > 0 && (
                  <div className="trace-args">
                    <span className="trace-args-label">פרמטרים:</span> {formatArgs(step.args)}
                  </div>
                )}

                <div className="trace-summary">{step.summary}</div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default AgentTrace;
