const DEMO_HEADER = 'x-demo-mode';

/** Satu sumber "sistem sedang di mode demo": dibaca dari header setiap respons server, atau dari status demo saat halaman dibuka. */
class DemoMode {
	active = $state(false);

	/** Respons yang membawa header berarti demo menyala; respons tanpa header berarti sudah kembali ke data asli. */
	observe(headers: Headers): void {
		this.active = headers.get(DEMO_HEADER) === '1';
	}

	set(active: boolean): void {
		this.active = active;
	}
}

export const demoMode = new DemoMode();
