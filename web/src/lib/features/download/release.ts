import { env } from '$env/dynamic/public';
import { format } from '$lib/text/format';
import { downloadText } from '$lib/text/download';
import { APK_NOTES, APK_VERSION, IOS_NOTES, IOS_VERSION } from '$lib/text/release-notes';

export type ReleaseNote = { icon: string; text: string };

/** The Android app on offer; the version is the versionName of the app. */
export const RELEASE = { version: APK_VERSION };

/** The employee web app on iPhone and iPad; the version is the one of the employee web. */
export const IOS_RELEASE = { version: IOS_VERSION };

/** What changed in this APK, the same list the tablet shows as "Yang baru". */
export const RELEASE_NOTES: ReleaseNote[] = APK_NOTES;

/** What changed in the employee web app, the same list it shows as "Yang baru". */
export const IOS_RELEASE_NOTES: ReleaseNote[] = IOS_NOTES;

/** One name for the APK, both as the file in the apk folder and as it is saved on the phone. */
export const APK_NAME = format(downloadText.apkFileName, { name: downloadText.appName, version: RELEASE.version });

export const APK_URL = `/apk/${encodeURIComponent(APK_NAME)}`;

export type AndroidFile = { sizeMb: number };

const BYTES_PER_MB = 1024 * 1024;

/** The published APK, asked from the server so nobody types its size by hand; null until its file is placed in the apk folder under APK_NAME. */
export async function androidFile(): Promise<AndroidFile | null> {
	const answer = await fetch(APK_URL, { method: 'HEAD' });
	const bytes = Number(answer.headers.get('content-length'));
	if (!answer.ok || !Number.isFinite(bytes) || bytes <= 0) return null;
	return { sizeMb: Math.round((bytes / BYTES_PER_MB) * 10) / 10 };
}

/** The employee web app installed from Safari on iPhone and iPad. */
export const IOS_WEB_URL: string | null = env.PUBLIC_PWA_URL || null;

/** The oldest Android the APK installs on (minSdk 26 in the app). */
export const ANDROID_MINIMUM = downloadText.androidMinimum;
