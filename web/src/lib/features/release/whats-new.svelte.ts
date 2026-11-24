import { api } from '$lib/api';
import { WEB_RELEASE } from './release';

export class WhatsNewState {
	open = $state(false);

	async load(): Promise<void> {
		// Gagal membaca berarti tidak ditampilkan sekarang; ringkasan dicoba lagi saat web dibuka berikutnya.
		const state = await api.releases.read(WEB_RELEASE.version).catch(() => null);
		this.open = state !== null && !state.read;
	}

	close(): void {
		this.open = false;
		void api.releases.markRead(WEB_RELEASE.version).catch(() => {});
	}
}
