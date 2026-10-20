import { describe, expect, it } from 'vitest';
import { cleanPickedPaths, cleanSavePick, nativePickerAvailable, nativeSaveAvailable } from './nativePicker';

describe('nativePicker', () => {
  it('is available only when the js_api exposes pick_files', () => {
    expect(nativePickerAvailable(undefined)).toBe(false);
    expect(nativePickerAvailable({})).toBe(false);
    expect(nativePickerAvailable({ pywebview: { api: {} } })).toBe(false);
    expect(nativePickerAvailable({ pywebview: { api: { pick_files: async () => [] } } })).toBe(true);
  });
  it('keeps only non-empty string paths', () => {
    expect(cleanPickedPaths(['C:\\a.tif', '', 3, null, '/b.tif'])).toEqual(['C:\\a.tif', '/b.tif']);
    expect(cleanPickedPaths(null)).toEqual([]);
    expect(cleanPickedPaths('x')).toEqual([]);
  });
});

describe('save picker helpers', () => {
  it('is available only when the js_api exposes pick_save', () => {
    expect(nativeSaveAvailable(undefined)).toBe(false);
    expect(nativeSaveAvailable({ pywebview: { api: { pick_files: async () => [] } } })).toBe(false);
    expect(nativeSaveAvailable({ pywebview: { api: { pick_save: async () => ({}) } } })).toBe(true);
  });
  it('keeps a pick only with both a folder and a name', () => {
    expect(cleanSavePick({ folder: '/a/b', name: 'x' })).toEqual({ folder: '/a/b', name: 'x' });
    expect(cleanSavePick({})).toBeNull();
    expect(cleanSavePick({ folder: '/a', name: '' })).toBeNull();
    expect(cleanSavePick(null)).toBeNull();
  });
});
