import { useEffect, useMemo, useState } from 'react';
import type { Analysis, EmbeddedRoi, Region } from '../api/types';
import { polygonArea, polygonBounds, rectPolygon } from '../lib/geometry';
import { liveObjects, useApp } from '../state/store';
import {
  coverageState,
  defaultGrid,
  describeIssues,
  exclusionCoverage,
  fieldIssues,
  fromApiGrid,
  generateGrid,
  hasIssues,
  storedGridCells,
  toApiGrid,
  MAX_FIELD,
  type GridOrder,
  type GridSpec,
  type StartCorner,
} from '../lib/labgrid';
import { NumInput } from './DetectTab';
import { ChamberSection, ReferenceSection } from './ReferencePanel';
import { regionStatus, STATUS_COLOR } from './Overlay';

export function StatusBadge({ region }: { region: Region }) {
  const st = regionStatus(region);
  return (
    <span className="chip" style={{ borderColor: STATUS_COLOR[st], color: STATUS_COLOR[st] }} data-testid={`region-status-${region.id}`}>
      {st}
    </span>
  );
}

export function RegionsTab() {
  const a = useApp((s) => s.current)!;
  const selectedId = useApp((s) => s.selectedRegionId);
  const setTool = useApp((s) => s.setTool);
  const showSug = useApp((s) => s.showSuggestions);
  const patch = useApp((s) => s.patch);
  const saveRegions = useApp((s) => s.saveRegions);
  const locked = a.status === 'finalized';
  const counting = a.regions.filter((r) => r.kind === 'counting');
  const excl = a.regions.filter((r) => r.kind === 'exclusion');
  const rois = a.image?.embedded_rois ?? [];

  const adopt = (roi: EmbeddedRoi, i: number, kind: 'counting' | 'exclusion') => {
    const region: Region = {
      id: 'reg-' + Date.now().toString(36) + i,
      kind,
      name: roi.name || `${kind === 'counting' ? 'Region' : 'Exclusion'} from ROI ${i + 1}`,
      polygon: rectPolygon(roi.left, roi.top, roi.right, roi.bottom),
      approved: false,
      approved_at: null,
      approval_fingerprint: null,
      inspected: false,
    };
    void saveRegions([...a.regions, region]);
    patch({ selectedRegionId: region.id });
  };

  return (
    <div className="regions" data-testid="regions-tab">
      <div className="row between">
        <h3>Regions</h3>
        <div className="row">
          <button className="btn sm" disabled={locked} onClick={() => setTool('draw-count-rect')}>
            + Counting
          </button>
          <button className="btn sm" disabled={locked} onClick={() => setTool('draw-excl-rect')}>
            + Exclusion
          </button>
        </div>
      </div>
      <div className="muted small">
        Counts are only reported for counting regions. Exclusion masks remove areas (edges, debris) from counting. Select a region to edit vertices: drag a
        vertex, double-click an edge to add one, Alt+click a vertex to remove it.
      </div>
      <FieldSummary />
      {!locked && <GridGenerator />}
      <ReferenceSection />
      {!locked && <ChamberSection />}
      {a.regions.length === 0 && (
        <div className="empty">
          No regions yet. With no counting region the whole image is detected, but at least one counting region is required to finalize. Use the toolbar to draw one.
        </div>
      )}
      {counting.map((r) => (
        <RegionCard key={r.id} region={r} selected={selectedId === r.id} locked={locked} />
      ))}
      {excl.length > 0 && <h4>Exclusion masks</h4>}
      {excl.map((r) => (
        <RegionCard key={r.id} region={r} selected={selectedId === r.id} locked={locked} />
      ))}
      {rois.length > 0 && (
        <section className="suggestions" data-testid="roi-suggestions">
          <div className="row between">
            <h4>Embedded ROIs (suggestions)</h4>
            <label className="chk small">
              <input type="checkbox" checked={showSug} onChange={(e) => patch({ showSuggestions: e.target.checked })} /> show
            </label>
          </div>
          <div className="muted small">Found inside the TIFF. Their meaning is not assumed and they are never applied automatically. Adopt one explicitly if it is right.</div>
          <ul className="sug-list">
            {rois.map((r, i) => (
              <li key={i}>
                <div>
                  <strong>{r.name || `ROI ${i + 1}`}</strong> <span className="muted">({r.source}, {r.roi_type})</span>
                  <div className="mono small muted">
                    bbox {r.left},{r.top} → {r.right},{r.bottom}
                  </div>
                  {r.roi_type.toLowerCase() !== 'rect' && r.roi_type.toLowerCase() !== 'rectangle' && (
                    <div className="small warn-text">Only the bounding box is available; adopting creates a rectangle.</div>
                  )}
                </div>
                <div className="row">
                  <button className="btn sm" disabled={locked} onClick={() => adopt(r, i, 'counting')}>
                    Adopt as counting
                  </button>
                  <button className="btn sm" disabled={locked} onClick={() => adopt(r, i, 'exclusion')}>
                    as exclusion
                  </button>
                </div>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}

function RegionCard({ region: r, selected, locked }: { region: Region; selected: boolean; locked: boolean }) {
  const a = useApp((s) => s.current)!;
  const counts = useApp((s) => s.counts);
  const err = useApp((s) => s.regionErrors[r.id]);
  const act = useApp((s) => s.act);
  const patch = useApp((s) => s.patch);
  const saveRegions = useApp((s) => s.saveRegions);
  const zoomBox = useApp((s) => s.zoomToBox);
  const [name, setName] = useState(r.name);
  const [editing, setEditing] = useState(false);
  const live = liveObjects(a).filter((o) => o.region_id === r.id);
  const unreviewed = live.filter((o) => !o.reviewed).length;
  const c = counts?.regions.find((x) => x.scope === r.id);
  const area = polygonArea(r.polygon);
  const isCounting = r.kind === 'counting';

  const rename = () => {
    setEditing(false);
    const n = name.trim() || r.name;
    setName(n);
    if (n !== r.name) void saveRegions(a.regions.map((x) => (x.id === r.id ? { ...x, name: n } : x)));
  };
  const remove = () => {
    if (!confirm(`Delete ${r.kind} region "${r.name}"?`)) return;
    void saveRegions(a.regions.filter((x) => x.id !== r.id));
  };

  return (
    <article className={`rcard ${selected ? 'sel' : ''}`} data-testid={`region-${r.id}`} aria-label={`Region ${r.name}`}>
      <header className="rhead" onClick={() => patch({ selectedRegionId: selected ? null : r.id })}>
        {editing ? (
          <input
            className="input sm"
            autoFocus
            value={name}
            onClick={(e) => e.stopPropagation()}
            onChange={(e) => setName(e.target.value)}
            onBlur={rename}
            onKeyDown={(e) => {
              if (e.key === 'Enter') rename();
              if (e.key === 'Escape') {
                setName(r.name);
                setEditing(false);
              }
            }}
            data-testid="region-name-input"
          />
        ) : (
          <strong
            className="rname"
            onDoubleClick={(e) => {
              e.stopPropagation();
              if (!locked) setEditing(true);
            }}
            title="Double-click to rename"
          >
            {r.name}
          </strong>
        )}
        <span className="chip">{r.kind}</span>
      </header>
      <div className="rmeta small muted mono">
        {Math.round(area).toLocaleString()} px² · {live.length} object{live.length === 1 ? '' : 's'}
        {isCounting && unreviewed > 0 ? ` · ${unreviewed} unreviewed` : ''}
        {c ? ` · R${c.red_only} G${c.green_only} Y${c.yellow} ?${c.uncertain}` : ''}
      </div>
      {isCounting && <FieldNumber region={r} locked={locked} />}
      {isCounting && (
        <div className="row wrap">
          <button
            className="btn sm"
            disabled={locked}
            title="Mark all non-deleted, non-uncertain objects in this region as reviewed"
            onClick={() => void act('accept_region', { region_id: r.id })}
            data-testid={`accept-${r.id}`}
          >
            Accept all proposals
          </button>
        </div>
      )}
      {err && (
        <div className="notice err small" role="alert" data-testid={`region-error-${r.id}`}>
          Refused: {err}
        </div>
      )}
      <div className="row wrap">
        <button
          className="btn sm ghost"
          onClick={() => {
            const b = polygonBounds(r.polygon);
            patch({ selectedRegionId: r.id });
            zoomBox(b.x0, b.y0, b.x1, b.y1);
          }}
        >
          Zoom to
        </button>
        <button className="btn sm ghost" disabled={locked} onClick={() => setEditing(true)}>
          Rename
        </button>
        <button className="btn sm ghost danger-hover" disabled={locked} onClick={remove} data-testid={`delete-region-${r.id}`}>
          Delete
        </button>
      </div>
    </article>
  );
}

const NOTE = 'No region = BLANK cell, region with 0 objects = 0 in the lab export.';

function exclusionPolys(regions: Region[]) {
  return regions.filter((r) => r.kind === 'exclusion').map((r) => r.polygon);
}

/** Lab-field overview: the blank-vs-zero rule and any numbering problems across existing regions. */
function FieldSummary() {
  const a = useApp((s) => s.current)!;
  const fields = a.regions.filter((r) => r.kind === 'counting' && r.field_index != null);
  const issues = fieldIssues(fields.map((r) => r.field_index), Infinity);
  const msgs = describeIssues(issues);
  const excl = exclusionPolys(a.regions);
  const partial = fields.filter((r) => coverageState(exclusionCoverage(r.polygon, excl)) === 'partial');
  const unnumbered = a.regions.filter((r) => r.kind === 'counting' && r.field_index == null).length;
  return (
    <div className="notice small" data-testid="field-note">
      <strong>{NOTE}</strong> Only regions with a field number are grid fields; at most {MAX_FIELD} can be counted for the CSV.
      {fields.length > 0 && <div data-testid="field-count">{fields.length} lab field{fields.length > 1 ? 's' : ''} defined.</div>}
      {unnumbered > 0 && <div>{unnumbered} counting region{unnumbered > 1 ? 's have' : ' has'} no field number (not exported in the lab layout).</div>}
      {msgs.length > 0 && (
        <div className="warn-text" role="alert" data-testid="field-issues">
          {msgs.join('; ')}.
        </div>
      )}
      {partial.length > 0 && (
        <div className="warn-text" data-testid="field-partial">
          Partially covered by an exclusion (count is over the remaining area): {partial.map((r) => r.name).join(', ')}.
        </div>
      )}
    </div>
  );
}

function FieldNumber({ region: r, locked }: { region: Region; locked: boolean }) {
  const a = useApp((s) => s.current)!;
  const saveRegions = useApp((s) => s.saveRegions);
  const others = a.regions.filter((x) => x.id !== r.id && x.kind === 'counting').map((x) => x.field_index);
  const fi = r.field_index ?? null;
  const dup = fi != null && others.includes(fi);
  const bad = fi != null && (!Number.isInteger(fi) || fi < 1);
  return (
    <div className="row wrap small">
      <label className="row">
        Field number
        <NumInput
          value={fi}
          nullable
          min={1}
          step={1}
          disabled={locked}
          testid={`field-index-${r.id}`}
          onChange={(v) => {
            const n = v == null ? null : Math.round(v);
            if (n !== fi) void saveRegions(a.regions.map((x) => (x.id === r.id ? { ...x, field_index: n } : x)));
          }}
        />
      </label>
      {fi == null && <span className="muted">none (not a lab field)</span>}
      {dup && <span className="warn-text" data-testid={`field-dup-${r.id}`}>duplicate field number</span>}
      {bad && <span className="warn-text" data-testid={`field-bad-${r.id}`}>must be a whole number ≥ 1</span>}
    </div>
  );
}

/** The form edits the BASE grid (no shift): a stored grid is loaded without its random shift. */
const formGrid = (a: Analysis): GridSpec =>
  a.slide.grid ? { ...fromApiGrid(a.slide.grid), seed: null, shiftDx: 0, shiftDy: 0 } : defaultGrid(a.image?.width ?? 2212, a.image?.height ?? 1264);

function GridGenerator() {
  const a = useApp((s) => s.current)!;
  const patch = useApp((s) => s.patch);
  const putGrid = useApp((s) => s.putGrid);
  const setTool = useApp((s) => s.setTool);
  const tool = useApp((s) => s.tool);
  const toast = useApp((s) => s.toast);
  const [open, setOpen] = useState(false);
  const [g, setG] = useState<GridSpec>(() => formGrid(a));
  const [mode, setMode] = useState<'replace' | 'add'>('replace');
  useEffect(() => {
    setG(formGrid(a));
    patch({ gridPreview: null });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [a.id]);
  const stored = a.slide.grid ?? null;
  const storedCells = storedGridCells(a);
  const nOn = storedCells.filter((c) => c.state === 'on').length;
  useEffect(() => () => patch({ gridPreview: null }), [patch]);

  const existingFields = a.regions.filter((r) => r.kind === 'counting' && r.field_index != null);
  const kept = mode === 'replace' ? a.regions.filter((r) => !(r.kind === 'counting' && r.field_index != null)) : a.regions;
  const cells = useMemo(() => generateGrid(g), [g]);
  const excl = exclusionPolys(a.regions);
  const cover = cells.map((c) => coverageState(exclusionCoverage(c.polygon, excl)));
  const W = a.image?.width ?? Infinity;
  const H = a.image?.height ?? Infinity;
  const outside = cells.filter((c) => c.polygon.some(([x, y]) => x < -0.5 || y < -0.5 || x > W - 0.5 || y > H - 0.5)).length;
  const issues = fieldIssues([...cells.map((c) => c.index), ...kept.filter((r) => r.kind === 'counting').map((r) => r.field_index)], Infinity);
  const blocked = hasIssues(issues) || cells.length === 0 || g.cellW <= 0 || g.cellH <= 0;
  const partial = cover.filter((c) => c === 'partial').length;
  const full = cover.filter((c) => c === 'full').length;

  const set = (p: Partial<GridSpec>) => setG((x) => ({ ...x, ...p }));
  const showPreview = () => {
    patch({ gridPreview: cells.map((c, i) => ({ index: c.index, polygon: c.polygon, flag: cover[i] !== 'none' })), showRegions: true });
  };
  // keep the on-image preview live while the panel is open and a preview is showing
  const previewOn = useApp((s) => s.gridPreview) != null;
  useEffect(() => {
    if (open && previewOn) showPreview();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cells, cover.join(',')]);

  // Apply = this exact grid (no shift). Fields keep their on/off choice by number; a field whose polygon does not
  // move keeps its approval (the server decides, see PUT /grid).
  const apply = async () => {
    if (blocked) return;
    const msg =
      mode === 'replace'
        ? `Replace ${existingFields.length} existing field region(s) with ${cells.length} Field-N regions? Fields that move lose their approvals/inspections; switched-off fields stay off.`
        : `Add ${cells.length} Field-N regions to the ${a.regions.length} existing region(s)?`;
    if (!confirm(msg)) return;
    const next = await putGrid({ grid: toApiGrid({ ...g, seed: null, shiftDx: 0, shiftDy: 0 }), replace: mode === 'replace' });
    if (!next) return;
    patch({ gridPreview: null });
    setTool('grid-pick');
    toast('success', `${cells.length}-field grid applied. Click fields to count them; click again to skip.`);
  };
  // Randomise = the grid stays where it is; the server draws a new random selection of up to 24 counted fields
  // (and records the seed).
  const randomise = async () => {
    if (blocked) return;
    if (!confirm(`Pick a new random selection of ${Math.min(MAX_FIELD, cells.length)} counted fields? Your current on/off choices are replaced (Ctrl+Z undoes).`)) return;
    const next = await putGrid({ grid: toApiGrid({ ...g, seed: null, shiftDx: 0, shiftDy: 0 }), randomise: true, replace: mode === 'replace' });
    if (!next?.slide.grid) return;
    patch({ gridPreview: null });
    setTool('grid-pick');
    const s = next.slide.grid;
    toast('success', `New random selection of counted fields (seed ${s.seed}). Ctrl+Z undoes.`);
  };
  const remove = async () => {
    if (!stored) return;
    if (!confirm(`Remove the grid and its ${nOn} unapproved field region(s)? (refused while a field is approved)`)) return;
    if (await putGrid({ grid: null })) setTool('select');
  };

  const num = (label: string, key: keyof GridSpec, min = 0, step = 1) => (
    <label>
      {label}
      <NumInput value={g[key] as number} min={min} step={step} testid={`grid-${key}`} onChange={(v) => set({ [key]: v ?? (g[key] as number) } as Partial<GridSpec>)} />
    </label>
  );

  return (
    <section className="gridgen" data-testid="grid-generator">
      <div className="row between">
        <h4>Grid fields</h4>
        <button className="btn sm" onClick={() => setOpen(!open)} aria-expanded={open} data-testid="grid-toggle">
          {open ? 'Close' : 'Generate grid…'}
        </button>
      </div>
      {stored && (
        <div className="row wrap small" data-testid="grid-stored">
          <span className="mono">
            {stored.rows} × {stored.cols} grid · {nOn} of {storedCells.length} fields counted
            {stored.seed != null ? ` · random selection (seed ${stored.seed})` : ''}
          </span>
          <button
            className={`btn sm${tool === 'grid-pick' ? ' primary' : ''}`}
            onClick={() => setTool(tool === 'grid-pick' ? 'select' : 'grid-pick')}
            aria-pressed={tool === 'grid-pick'}
            data-testid="grid-pick"
          >
            {tool === 'grid-pick' ? 'Done picking' : 'Pick fields'}
          </button>
          <button className="btn sm ghost" onClick={() => void remove()} data-testid="grid-remove">
            Remove grid
          </button>
        </div>
      )}
      {tool === 'grid-pick' && (
        <div className="muted small" data-testid="grid-pick-help">
          Click fields to count them; click again to skip. Keys: A all, N none, I invert. Esc leaves.
        </div>
      )}
      {open && (
        <>
          <div className="muted small">
            Creates counting regions named Field-N (field number N) on a rows × columns grid. The lab template has fields 1–24, so the grid can have at most 24 cells (default 4 × 6 of about 316 px, centred on the image); check the preview against the picture. After Apply, click fields on the image to switch them on/off for counting.
          </div>
          <div className="form-grid">
            {num('Rows', 'rows', 1)}
            {num('Columns', 'cols', 1)}
            {num('Cell width (px)', 'cellW', 1)}
            {num('Cell height (px)', 'cellH', 1)}
            {num('Origin x (px)', 'originX', -100000)}
            {num('Origin y (px)', 'originY', -100000)}
            <label>
              Numbering order
              <select className="input sm" value={g.order} onChange={(e) => set({ order: e.target.value as GridOrder })} data-testid="grid-order">
                <option value="row-major">row-major (along rows)</option>
                <option value="col-major">column-major (down columns)</option>
              </select>
            </label>
            <label>
              Start corner
              <select className="input sm" value={g.corner} onChange={(e) => set({ corner: e.target.value as StartCorner })} data-testid="grid-corner">
                <option value="tl">top-left</option>
                <option value="tr">top-right</option>
                <option value="bl">bottom-left</option>
                <option value="br">bottom-right</option>
              </select>
            </label>
            {num('First field index', 'firstIndex', 1)}
            <label>
              Existing field regions
              <select className="input sm" value={mode} onChange={(e) => setMode(e.target.value as 'replace' | 'add')} data-testid="grid-mode">
                <option value="replace">replace ({existingFields.length})</option>
                <option value="add">add alongside</option>
              </select>
            </label>
          </div>
          <div className="notice warn small" data-testid="grid-order-note">
            Numbering order is a choice; confirm with your lab convention. The app does not know how your fields are numbered.
          </div>
          <div className="small mono muted" data-testid="grid-summary">
            {cells.length} cells · Field-{g.firstIndex} … Field-{g.firstIndex + cells.length - 1}
          </div>
          {describeIssues(issues).length > 0 && (
            <div className="notice err small" role="alert" data-testid="grid-issues">
              Cannot apply or randomise: {describeIssues(issues).join('; ')}.
            </div>
          )}
          {outside > 0 && <div className="small warn-text">{outside} cell(s) extend beyond the image.</div>}
          {cells.length > MAX_FIELD && (
            <div className="small muted" data-testid="grid-many-note">
              {cells.length} cells cover the image; {MAX_FIELD} of them are counted, drawn at random from the cells fully on the image (edge cells that overhang stay off). Click fields to change the choice; Randomise draws again.
            </div>
          )}
          {(partial > 0 || full > 0) && (
            <div className="small warn-text" data-testid="grid-exclusion-warn">
              {partial > 0 ? `${partial} field(s) partially covered by an exclusion (count is over the remaining area)` : ''}
              {partial > 0 && full > 0 ? '; ' : ''}
              {full > 0 ? `${full} fully covered` : ''}. Flagged in amber in the preview.
            </div>
          )}
          <div className="row wrap">
            <button className="btn sm" onClick={showPreview} data-testid="grid-preview-btn">
              Preview on image
            </button>
            <button className="btn sm ghost" onClick={() => patch({ gridPreview: null })}>
              Hide preview
            </button>
            <button className="btn sm primary" disabled={blocked} onClick={() => void apply()} data-testid="grid-apply">
              Apply ({cells.length} regions)
            </button>
            <button
              className="btn sm"
              disabled={blocked || !a.image}
              onClick={() => void randomise()}
              title="The grid stays where it is; a new random selection of up to 24 fields is counted"
              data-testid="grid-randomise"
            >
              Randomise
            </button>
          </div>
        </>
      )}
    </section>
  );
}
