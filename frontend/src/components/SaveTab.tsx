import { useEffect, useMemo, useState } from 'react';
import { nativeSaveAvailable, pickNativeSave } from '../lib/nativePicker';
import { api, ApiError } from '../api/client';
import type { CountClass, SaveSlideReport } from '../api/types';
import { MAX_FIELD } from '../lib/labgrid';
import { COUNT_CLASSES, dirOf, gridFields, selectionProblems } from '../lib/saveslide';
import { useApp } from '../state/store';

const CLASS_TEXT: Record<CountClass, string> = { red: 'red only', green: 'green only', yellow: 'yellow (red + green)' };
const ONE_COLOURS: CountClass[][] = COUNT_CLASSES.map((c) => [c]);
const COMBOS: { classes: CountClass[]; text: string }[] = [
  { classes: ['red', 'yellow'], text: 'red + yellow together' },
  { classes: ['green', 'yellow'], text: 'green + yellow together' },
];

/** The researcher's Save: choose what to count, which grid fields count, then write the labelled scan + CSVs. */
export function SaveTab() {
  const a = useApp((s) => s.current)!;
  const sel = useApp((s) => s.saveSel);
  const patch = useApp((s) => s.patch);
  const toast = useApp((s) => s.toast);
  const [outDir, setOutDir] = useState('');
  const [fileName, setFileName] = useState('');
  const [training, setTraining] = useState(true);
  const [busy, setBusy] = useState(false);
  const [report, setReport] = useState<SaveSlideReport | null>(null);
  const [error, setError] = useState('');
  const src = a.image?.source_path ?? null;
  const fields = useMemo(() => gridFields(a), [a]);
  const counted = fields.filter((f) => f.counted).length;
  const problems = [
    ...selectionProblems(sel),
    ...(counted > MAX_FIELD ? [`${counted} fields are counted but the CSV has room for ${MAX_FIELD}: switch ${counted - MAX_FIELD} off, or use Randomise in the Regions tab.`] : []),
  ];
  // the experiment's folder (picked once when the experiment was created); the server uses it when no folder is sent
  const expId = a.experiment_id ?? null;
  const [expDir, setExpDir] = useState<string | null>(null);
  useEffect(() => {
    let live = true;
    setExpDir(null);
    if (expId) api.getExperiment(expId).then((e) => live && setExpDir(e.save_dir ?? null), () => undefined);
    return () => { live = false; };
  }, [expId]);
  const needDir = !src && !outDir.trim() && !expDir;
  const native = nativeSaveAvailable();
  const defaultName = src ? (src.split(/[\\/]/).pop() ?? '').replace(/\.[^.]+$/, '') : a.name;
  const choose = async () => {
    const p = await pickNativeSave(fileName || defaultName, outDir || (src ? dirOf(src) : ''));
    if (p) {
      setOutDir(p.folder);
      setFileName(p.name);
    }
  };

  const same = (x: CountClass[], y: CountClass[]) => x.length === y.length && x.every((c) => y.includes(c));
  const hasSel = (cs: CountClass[]) => sel.some((r) => same(r.classes, cs));
  /** Tick/untick a row; the rows stay in the order of ONE_COLOURS, then COMBOS. */
  const toggleSel = (cs: CountClass[]) => {
    const kept = hasSel(cs) ? sel.filter((r) => !same(r.classes, cs)) : [...sel, { classes: cs }];
    const rank = (r: { classes: CountClass[] }) => [...ONE_COLOURS, ...COMBOS.map((c) => c.classes)].findIndex((x) => same(x, r.classes));
    patch({ saveSel: [...kept].sort((x, y) => rank(x) - rank(y)) });
  };

  const save = async () => {
    setBusy(true);
    setError('');
    setReport(null);
    try {
      const r = await api.saveSlide(a.id, sel, outDir.trim() || undefined, fileName.trim() || undefined, training);
      setReport(r);
      toast('success', `Saved ${r.files.length} files to ${r.directory}`);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="savetab" data-testid="save-tab">
      <h3>Save</h3>
      <div className="muted small">
        Writes the scan with your labels and the counts as CSV files. Check and correct the labels first (Review tab); Save can be repeated and replaces the earlier result.
      </div>

      <section>
        <h4>1. What to count</h4>
        <div className="muted small">Each ticked colour becomes its own row in the CSV (with a Color column).</div>
        <div className="row wrap">
          {COUNT_CLASSES.map((c) => (
            <label className="chk small" key={c}>
              <input type="checkbox" checked={hasSel([c])} onChange={() => toggleSel([c])} data-testid={`save-${c}`} /> {CLASS_TEXT[c]}
            </label>
          ))}
        </div>
        <div className="muted small">Also as a combined row (the lab’s “positive” counts):</div>
        <div className="row wrap">
          {COMBOS.map((c) => (
            <label className="chk small" key={c.classes.join('+')}>
              <input type="checkbox" checked={hasSel(c.classes)} onChange={() => toggleSel(c.classes)} data-testid={`save-combo-${c.classes.join('-')}`} /> {c.text}
            </label>
          ))}
        </div>
      </section>

      <section>
        <h4>
          2. Grid fields to count{' '}
          <span className="muted small" data-testid="save-grid-count">
            ({counted} of {fields.length})
          </span>
        </h4>
        {fields.length === 0 ? (
          <div className="empty">No grid yet. Open the Regions tab → “Generate grid…” to add the grid (same size as in ImageJ).</div>
        ) : (
          <>
            <GridMap />
            <div className="muted small">Click a field to switch it off (bad area) or on. A field that is off stays empty in the CSV; a counted field with no polonies is 0.</div>
          </>
        )}
      </section>

      <section>
        <h4>3. Where</h4>
        {expDir && !outDir ? (
          <div className="small" data-testid="save-where">
            Experiment folder: <span className="mono">{expDir}</span> <span className="muted">(set on the experiment page)</span>
          </div>
        ) : src && !outDir ? (
          <div className="small" data-testid="save-where">
            Next to the original: <span className="mono">{dirOf(src)}</span>
          </div>
        ) : outDir && native ? (
          <div className="small" data-testid="save-where">
            Folder: <span className="mono">{outDir}</span>
          </div>
        ) : null}
        {native ? (
          <div className="row wrap">
            <button className="btn sm" onClick={() => void choose()} data-testid="save-choose">
              {outDir || src || expDir ? 'Choose another folder and name…' : 'Choose folder and file name…'}
            </button>
            {fileName && (
              <span className="small">
                File name: <span className="mono">{fileName}</span>
              </span>
            )}
          </div>
        ) : (
          !src && !expDir && (
            <label className="small">
              This scan was uploaded, so its folder is unknown. Folder to save in:
              <input className="input sm" value={outDir} onChange={(e) => setOutDir(e.target.value)} placeholder="/path/to/folder" data-testid="save-outdir" />
            </label>
          )
        )}
      </section>

      <label className="chk small" data-testid="save-training-row">
        <input type="checkbox" checked={training} onChange={(e) => setTraining(e.target.checked)} data-testid="save-training" /> Also save training data (images + corrected points, an
        immutable dataset snapshot in a <span className="mono">training</span> folder next to the results)
      </label>

      {problems.length > 0 && (
        <div className="notice warn small" role="alert">
          {problems.join(' ')}
        </div>
      )}
      <button className="btn primary" disabled={busy || problems.length > 0 || counted === 0 || needDir} onClick={() => void save()} data-testid="save-btn">
        {busy ? 'Saving…' : 'Save'}
      </button>
      {error && (
        <div className="notice err small" role="alert" data-testid="save-error">
          {error}
        </div>
      )}
      {report && (
        <div className="notice ok small" data-testid="save-report">
          <strong>Saved</strong> in <span className="mono">{report.directory}</span>
          <ul>
            {report.files.map((f) => (
              <li key={f} className="mono">
                {f}
              </li>
            ))}
          </ul>
          {report.rows.map((r) => (
            <div key={r.what_counted}>
              {r.what_counted}: {r.nofpol} polonies in {r.nofgrids} fields
            </div>
          ))}
          {report.training && (
            <div className={report.training.status === 'ok' ? '' : 'warn-text'} data-testid="save-training-report">
              Training data: {report.training.message}
              {report.training.directory && (
                <>
                  {' '}
                  (<span className="mono">{report.training.directory}</span>)
                </>
              )}
            </div>
          )}
          {report.warnings.map((w) => (
            <div key={w} className="warn-text">
              {w}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/** Small map of the grid: each field is a clickable cell placed where it lies on the image. */
function GridMap() {
  const a = useApp((s) => s.current)!;
  const setAnalysis = useApp((s) => s.setAnalysis);
  const toast = useApp((s) => s.toast);
  const fields = useMemo(() => gridFields(a), [a]);
  const locked = a.status === 'finalized';
  const W = a.image?.width ?? 1;
  const H = a.image?.height ?? 1;
  const toggle = async (field: number, counted: boolean) => {
    try {
      setAnalysis(await api.setGridField(a.id, field, counted));
      void useApp.getState().refreshDerived();
    } catch (e) {
      toast('error', `grid field ${field}: ${e instanceof ApiError ? e.message : String(e)}`);
    }
  };
  return (
    <svg className="gridmap" viewBox={`0 0 ${W} ${H}`} role="group" aria-label="Grid fields" data-testid="grid-map">
      <rect x={0} y={0} width={W} height={H} className="gridmap-bg" />
      {fields.map((f) => {
        const xs = f.polygon.map((p) => p[0]);
        const ys = f.polygon.map((p) => p[1]);
        const x0 = Math.min(...xs), y0 = Math.min(...ys);
        const w = Math.max(...xs) - x0, h = Math.max(...ys) - y0;
        return (
          <g
            key={f.field}
            className={`gridmap-cell ${f.counted ? 'on' : 'off'}`}
            role="checkbox"
            aria-checked={f.counted}
            aria-label={`Field ${f.field}`}
            tabIndex={locked ? -1 : 0}
            data-testid={`grid-cell-${f.field}`}
            onClick={() => !locked && void toggle(f.field, !f.counted)}
            onKeyDown={(e) => (e.key === ' ' || e.key === 'Enter') && !locked && (e.preventDefault(), void toggle(f.field, !f.counted))}
          >
            <rect x={x0} y={y0} width={w} height={h} />
            <text x={x0 + w / 2} y={y0 + h / 2} textAnchor="middle" dominantBaseline="middle" style={{ fontSize: Math.max(12, Math.min(w, h) / 3) }}>
              {f.counted ? f.field : `${f.field} ✕`}
            </text>
          </g>
        );
      })}
    </svg>
  );
}
