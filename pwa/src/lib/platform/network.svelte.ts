import { browser } from '$app/environment';

/** Keadaan internet perangkat; "online" berarti browser menganggap perangkat terhubung ke jaringan. */
class NetworkMonitor {
	online = $state(browser ? navigator.onLine : true);

	constructor() {
		if (!browser) return;
		window.addEventListener('online', () => (this.online = true));
		window.addEventListener('offline', () => (this.online = false));
	}
}

export const network = new NetworkMonitor();
