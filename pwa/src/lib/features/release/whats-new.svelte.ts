import type { Schemas } from '$lib/api/contract';
import { current } from '$lib/auth/current.svelte';
import { PWA_RELEASE } from './release';

const BASE = '/v2/release-read';

export class WhatsNewState {
	open = $state(false);
	settled = $state(false);

	async load(onSessionExpired: () => void): Promise<void> {
		const result = await current.api().read<Schemas['ReleaseReadOut']>(BASE, { version: PWA_RELEASE.version });
		if (result.kind === 'unauthorized') onSessionExpired();
		this.open = result.kind === 'success' && !result.value.read;
		this.settled = true;
	}

	// Lembar langsung tertutup; gagal menandai hanya membuat ringkasan muncul lagi saat dibuka berikutnya.
	close(): void {
		this.open = false;
		void current.api().write('PATCH', BASE, { version: PWA_RELEASE.version });
	}
}
