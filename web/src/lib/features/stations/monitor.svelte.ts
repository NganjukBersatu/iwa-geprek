import { userMessage } from '$lib/api/user-message';
import { api } from '$lib/api';
import type { StationMonitor } from '$lib/api/types';
import { Filters } from '$lib/components/filter/filters.svelte';
import { STATION_TABLES } from '$lib/live/tables';
import { termText } from '$lib/text/terms';
import { stationText } from '$lib/text/stations';

export class MonitorState {
	readonly tables = STATION_TABLES;
	readonly filters = new Filters([{ kind: 'select', key: 'cabang', label: termText.branch, options: [] }]);

	loading = $state(true);
	error = $state('');
	data = $state<StationMonitor | null>(null);
	private token = 0;

	get branch(): string | null {
		return this.filters.get('cabang');
	}

	// Muat ulang tanpa mengosongkan layar, supaya sinyal live tidak membuat tabel berkedip.
	refresh(): Promise<void> {
		return this.load(true);
	}

	async load(quiet = false): Promise<void> {
		const token = ++this.token;
		if (!quiet) {
			this.loading = true;
			this.error = '';
		}
		try {
			const data = await api.stations.monitor({ outlet_id: this.branch });
			if (token === this.token) this.data = data;
		} catch (error) {
			if (token !== this.token || quiet) return;
			this.data = null;
			this.error = userMessage(error, stationText.monitorLoadFailed);
		} finally {
			if (token === this.token) this.loading = false;
		}
	}
}
