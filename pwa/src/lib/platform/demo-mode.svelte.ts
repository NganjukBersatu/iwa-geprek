const DEMO_HEADER = 'x-demo-mode';

/** Satu sumber "sistem sedang di mode demo" di PWA: dibaca dari header setiap respons server. */
class DemoMode {
	active = $state(false);

	/** Respons berheader demo berarti demo menyala; respons tanpa header berarti sudah kembali ke data asli. */
	observe(headers: Headers): void {
		this.active = headers.get(DEMO_HEADER) === '1';
	}
}

export const demoMode = new DemoMode();
