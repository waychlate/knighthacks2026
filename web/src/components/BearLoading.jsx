export default function BearLoading() {
  return (
    <div className="bear-loading" role="status" aria-live="polite">
      <div className="bear-loading-stage" aria-hidden="true">
        <span className="bear-paw bear-paw-1">🐾</span>
        <span className="bear-paw bear-paw-2">🐾</span>
        <span className="bear-paw bear-paw-3">🐾</span>
        <span className="bear-paw bear-paw-4">🐾</span>
        <svg className="bear-walker" viewBox="0 0 180 110" focusable="false">
          <g className="bear-body-bounce">
            <ellipse className="bear-body" cx="89" cy="59" rx="53" ry="29" />
            <circle className="bear-head" cx="140" cy="43" r="25" />
            <circle className="bear-ear" cx="126" cy="22" r="9" />
            <circle className="bear-ear" cx="151" cy="21" r="9" />
            <ellipse className="bear-muzzle" cx="158" cy="49" rx="13" ry="9" />
            <circle className="bear-eye" cx="149" cy="39" r="3" />
            <circle className="bear-nose" cx="168" cy="48" r="3.5" />
            <g className="bear-leg bear-leg-1"><rect x="50" y="72" width="16" height="30" rx="8" /><ellipse cx="57" cy="102" rx="12" ry="5" /></g>
            <g className="bear-leg bear-leg-2"><rect x="78" y="75" width="16" height="28" rx="8" /><ellipse cx="86" cy="103" rx="12" ry="5" /></g>
            <g className="bear-leg bear-leg-3"><rect x="111" y="72" width="16" height="30" rx="8" /><ellipse cx="119" cy="102" rx="12" ry="5" /></g>
            <path className="bear-tail" d="M38 54c-17-14-25-5-18 8 5 9 14 10 22 4" />
          </g>
        </svg>
      </div>
      <span className="bear-loading-label">Exploring the park…</span>
    </div>
  )
}
