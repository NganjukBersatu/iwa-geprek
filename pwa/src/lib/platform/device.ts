import { dev } from '$app/environment';

/** PWA ini hanya untuk iPhone dan iPad; Android, PC, laptop, dan Mac ditolak. Saat pengembangan semua perangkat boleh. */
const IOS = /iPhone|iPad|iPod/;
const MAC = /Macintosh/;

/** Tanda pengenal perangkat; di server `platform` dari header Sec-CH-UA-Platform dan `touchPoints` selalu -1 karena tidak diketahui. */
export type DeviceSignals = { userAgent: string; platform: string; touchPoints: number };

export function isBlockedDevice(device: DeviceSignals): boolean {
	if (dev) return false;
	// Safari dan semua browser di iOS tidak mengirim Sec-CH-UA-Platform; yang mengirimnya pasti Chromium di luar iOS.
	if (device.platform !== '') return true;
	if (IOS.test(device.userAgent)) return false;
	// iPad memakai tampilan desktop dan mengaku Macintosh; bedanya dari Mac hanya layar sentuh, yang baru terbaca di browser.
	if (MAC.test(device.userAgent)) return device.touchPoints >= 0 && device.touchPoints < 2;
	return true;
}

export function browserDevice(): DeviceSignals {
	const hints = (navigator as Navigator & { userAgentData?: { platform: string } }).userAgentData;
	return { userAgent: navigator.userAgent, platform: hints ? hints.platform || 'Chromium' : '', touchPoints: navigator.maxTouchPoints };
}
