import { api } from '$lib/api';
import type { Filters } from '$lib/components/filter/filters.svelte';
import { lastPickable, type DateRange } from '$lib/date/range';
import { whenChanged } from '$lib/stores/when-changed.svelte';

/**
 * Begitu satu cabang dipilih, filter Rentang langsung diisi periode cabang yang sedang berjalan,
 * atau rentang dari `pick` bila halaman itu butuh periode lain (misalnya periode yang harus ditutup).
 * Daftar periode per bulan sengaja tidak ditambahkan ke pilihan; rentang lain dipilih sendiri lewat pilihan rentang biasa.
 */
export function syncBranchPeriod(getFilters: () => Filters | undefined, pick?: (branchId: string) => Promise<DateRange | null>): void {
	whenChanged(
		() => getFilters()?.get('cabang') ?? null,
		(branchId) => {
			const filters = getFilters();
			const rentang = filters?.defs.find((def) => def.key === 'rentang');
			if (!filters || !branchId || rentang?.kind !== 'date') return;
			void Promise.all([api.outlets.periods(branchId), choose(pick, branchId)]).then(([periods, chosen]) => {
				// Jawaban untuk cabang yang sudah tidak dipilih lagi dibuang supaya tidak menimpa pilihan terbaru.
				if (filters.get('cabang') !== branchId) return;
				if (chosen) return filters.set('rentang', chosen);
				const running = periods.find((period) => period.running) ?? periods[0];
				if (!running) return;
				// Filter yang hanya menjangkau ke belakang berhenti di hari ini, karena hari depan belum punya angka.
				const last = lastPickable(rentang.reach);
				filters.set('rentang', { from: running.start, to: last !== null && running.end > last ? last : running.end });
			}, (problem: unknown) => {
				// Halaman tetap jalan dengan rentang yang sudah ada; hanya pengisian otomatisnya yang terlewat.
				console.warn('[periode] periode cabang gagal dimuat', problem);
			});
		}
	);
}

/** Pilihan khusus halaman yang gagal dimuat tidak menghalangi periode berjalan. */
async function choose(pick: ((branchId: string) => Promise<DateRange | null>) | undefined, branchId: string): Promise<DateRange | null> {
	if (!pick) return null;
	try {
		return await pick(branchId);
	} catch (problem) {
		console.warn('[periode] pilihan periode halaman gagal dimuat', problem);
		return null;
	}
}
