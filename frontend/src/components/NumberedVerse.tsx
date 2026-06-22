import React from 'react';
import { NumberedVerse as Verse } from '../api';

// Render a verse with a running number above each word (RTL: word 1 is rightmost).
// Splits on whitespace, maqaf (־, U+05BE) and paseq (׀, U+05C0) — matching how the
// backend counts words: maqaf-joined words are separate, and the paseq is not a
// word (it attaches to the preceding word, so we don't number it).
const NumberedVerse: React.FC<{ verse: Verse }> = ({ verse }) => {
  // Backend already collapses ketiv/qere; strip any stray parentheses defensively.
  const words = verse.text
    .split(/[\s־׀]+/)
    .map((w) => w.replace(/[()[\]]/g, ''))
    .filter(Boolean);
  return (
    <div className="numbered-verse rtl">
      <div className="nv-ref">
        {verse.ref} · {verse.word_count} מילים
      </div>
      <div className="nv-words">
        {words.map((w, i) => (
          <span className="nv-word" key={i}>
            <span className="nv-num">{i + 1}</span>
            <span className="nv-text">{w}</span>
          </span>
        ))}
      </div>
    </div>
  );
};

export default NumberedVerse;
