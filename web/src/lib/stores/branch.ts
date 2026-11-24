import { writable } from 'svelte/store';
import type { OutletOption } from '$lib/api/types';
import { getUser } from '$lib/auth/session';
import { fix, memoryKey, onRemember, recall, remember } from './memory';

const KEY = memoryKey.filter('cabang');

/** The branch every request is sent for; null means all branches. It follows the remembered `cabang` filter. */
export const selectedBranch = writable<string | null>(null);

export const branches = writable<OutletOption[]>([]);

function current(): string | null {
	const value = recall(KEY);
	return typeof value === 'string' ? value : null;
}

onRemember(KEY, () => selectedBranch.set(current()));

/** Loads the signed-in account's branch; an account tied to one branch always has that one. */
export function restoreBranch(): void {
	fix(KEY, getUser()?.outlet_id ?? null);
	selectedBranch.set(current());
	checked = recheck();
}

let checked: Promise<void> = Promise.resolve();

/** Selesai setelah cabang yang diingat dipastikan masih ada, supaya permintaan pertama tidak mengirim cabang yang sudah dihapus. */
export function branchChecked(): Promise<void> {
	return checked;
}

/** Cabang yang baru dihapus dari layar ini dilupakan seketika, tanpa menunggu daftar cabang dimuat ulang. */
export function forgetBranch(id: string): void {
	if (current() === id) remember(KEY, null);
}

/** Memuat daftar supaya cabang yang sudah dihapus terlupakan; gagal tidak disimpan, jadi layar berikutnya meminta lagi dan menampilkan galatnya. */
function recheck(): Promise<void> {
	return branchList().then(
		() => undefined,
		() => undefined
	);
}

/** A remembered branch missing from the full branch list was deleted, so it is forgotten. */
export function dropMissingBranch(outlets: OutletOption[]): void {
	const id = current();
	if (id && outlets.length > 0 && !outlets.some((outlet) => outlet.id === id)) remember(KEY, null);
}

// One list per signed-in account, asked for once and asked again only when the server says branches changed.
let loaded: { owner: string; list: Promise<OutletOption[]> } | null = null;
let watching = false;

/** Every branch the account may see; screens share one request instead of each asking on every load. */
export function branchList(): Promise<OutletOption[]> {
	const owner = getUser()?.id ?? '';
	if (loaded?.owner !== owner) loaded = { owner, list: fetchBranches() };
	return loaded.list;
}

async function fetchBranches(): Promise<OutletOption[]> {
	const [{ api }, { live }] = await Promise.all([import('$lib/api'), import('$lib/live/live')]);
	if (!watching) {
		watching = true;
		live.on(['outlets'], () => {
			loaded = null;
			void recheck();
		});
	}
	try {
		const outlets = await api.outlets.list();
		branches.set(outlets);
		return outlets;
	} catch (error) {
		// A failed request is not kept, so the next screen asks again.
		loaded = null;
		throw error;
	}
}

export async function loadBranchOptions(): Promise<{ value: string; label: string }[]> {
	return (await branchList()).map((outlet) => ({ value: outlet.id, label: outlet.name }));
}
