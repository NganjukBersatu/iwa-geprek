import { browser } from '$app/environment';
import { getUser } from '$lib/auth/session';

/** The one memory of what an account last picked in lists, kept per account in this browser: filters and rows per page are shared by every list, while the search and the page are kept per screen. */
const STORAGE_KEY = 'web.memory';

export type MemoryValue = string | number | { preset: string } | { from: string; to: string };

type Listener = (value: MemoryValue | null) => void;

export const memoryKey = {
	filter: (id: string): string => `filter.${id}`,
	search: (path: string): string => `cari.${path}`,
	pageSize: 'baris',
	page: (path: string, list: string): string => `halaman.${path}.${list}`,
	sort: (list: string): string => `urut.${list}`,
	guide: (id: string): string => `panduan.${id}`
};

/** Values the account may not change, such as the branch of an account tied to one branch. */
const fixed = new Map<string, MemoryValue>();
const listeners = new Map<string, Set<Listener>>();

function isValue(value: unknown): value is MemoryValue {
	if (typeof value === 'string' || typeof value === 'number') return true;
	if (!value || typeof value !== 'object') return false;
	const record = value as Record<string, unknown>;
	return typeof record.preset === 'string' || (typeof record.from === 'string' && typeof record.to === 'string');
}

function storageName(): string | null {
	const id = getUser()?.id;
	return browser && id ? `${STORAGE_KEY}.${id}` : null;
}

function load(): Record<string, MemoryValue> {
	const name = storageName();
	if (!name) return {};
	try {
		const parsed: unknown = JSON.parse(localStorage.getItem(name) ?? '{}');
		if (!parsed || typeof parsed !== 'object') return {};
		return Object.fromEntries(Object.entries(parsed).filter((entry): entry is [string, MemoryValue] => isValue(entry[1])));
	} catch {
		return {};
	}
}

function notify(key: string, value: MemoryValue | null): void {
	listeners.get(key)?.forEach((listener) => listener(value));
}

export function recall(key: string): MemoryValue | null {
	return fixed.get(key) ?? load()[key] ?? null;
}

/** Null or an empty text forgets the key, which every list reads as nothing picked. */
export function remember(key: string, value: MemoryValue | null): void {
	if (fixed.has(key)) return;
	const name = storageName();
	if (name) {
		const values = load();
		if (value === null || value === '') delete values[key];
		else values[key] = value;
		try {
			localStorage.setItem(name, JSON.stringify(values));
		} catch {
			// Storage can be blocked; the choice then lasts until the page closes.
		}
	}
	notify(key, value === '' ? null : value);
}

export function fix(key: string, value: MemoryValue | null): void {
	if (value === null) fixed.delete(key);
	else fixed.set(key, value);
	notify(key, recall(key));
}

export function onRemember(key: string, listener: Listener): () => void {
	const set = listeners.get(key) ?? new Set<Listener>();
	set.add(listener);
	listeners.set(key, set);
	return () => set.delete(listener);
}
