/** Native file picker exposed by the desktop window (pywebview js_api, see polony_app/launcher.py). */
export interface PywebviewApi {
  pick_files: () => Promise<unknown>;
  pick_save: (name: string, directory: string) => Promise<unknown>;
}

declare global {
  interface Window {
    pywebview?: { api?: Partial<PywebviewApi> };
  }
}

type MaybeWindow = { pywebview?: { api?: Partial<PywebviewApi> } } | undefined;

/** True only inside the native window, where `pick_files` exists. */
export function nativePickerAvailable(w: MaybeWindow = typeof window === 'undefined' ? undefined : window): boolean {
  return typeof w?.pywebview?.api?.pick_files === 'function';
}

/** Keep only non-empty string paths from whatever the Python side returned. */
export function cleanPickedPaths(raw: unknown): string[] {
  return Array.isArray(raw) ? raw.filter((p): p is string => typeof p === 'string' && p.length > 0) : [];
}

export async function pickNativeFiles(): Promise<string[]> {
  const api = window.pywebview?.api;
  return api && typeof api.pick_files === 'function' ? cleanPickedPaths(await api.pick_files()) : [];
}

export interface SavePick {
  folder: string;
  name: string;
}

/** True only inside the native window, where `pick_save` exists. */
export function nativeSaveAvailable(w: MaybeWindow = typeof window === 'undefined' ? undefined : window): boolean {
  return typeof w?.pywebview?.api?.pick_save === 'function';
}

/** Keep a picked folder + file name only when both are non-empty strings. */
export function cleanSavePick(raw: unknown): SavePick | null {
  const r = raw as Partial<SavePick> | null | undefined;
  return r && typeof r.folder === 'string' && r.folder && typeof r.name === 'string' && r.name ? { folder: r.folder, name: r.name } : null;
}

/** Native "save as" window (folder + file name); null when cancelled or not in the native window. */
export async function pickNativeSave(name: string, directory: string): Promise<SavePick | null> {
  const api = window.pywebview?.api;
  return api && typeof api.pick_save === 'function' ? cleanSavePick(await api.pick_save(name, directory)) : null;
}
