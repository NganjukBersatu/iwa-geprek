import { current } from '$lib/auth/current.svelte';
import type { AppFailure } from '$lib/failure/failure';

/** Perangkat operasional yang baru ditautkan. */
export type LinkedDevice = { name: string };

/** Menautkan karyawan ke perangkat operasional dengan QR yang tampil di perangkat itu. */
export class PairingState {
	scanning = $state(false);
	sending = $state(false);
	linked = $state<LinkedDevice | null>(null);
	failure = $state<AppFailure | null>(null);

	constructor(private readonly onSessionExpired: () => void) {}

	startScan(): void {
		this.failure = null;
		this.scanning = true;
	}

	stopScan(): void {
		this.scanning = false;
	}

	/** Pemindai memanggil berulang untuk QR yang sama; hanya yang pertama diproses. */
	async onScanned(qrToken: string): Promise<void> {
		if (!this.scanning || this.sending) return;
		this.scanning = false;
		this.sending = true;
		const result = await current.api().write<{ device_name: string }>('POST', '/v2/devices/link', { token: qrToken });
		this.sending = false;
		if (result.kind === 'success') this.linked = { name: result.value.device_name };
		else if (result.kind === 'unauthorized') this.onSessionExpired();
		else this.failure = result.failure;
	}
}
