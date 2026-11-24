import { chooseFile } from './photo';
import { VIDEO_MAX_BYTES } from './upload-limits';

const EXTENSIONS: Record<string, string> = { 'video/quicktime': '.mov', 'video/webm': '.webm' };
const DEFAULT_EXTENSION = '.mp4';

/** Satu video yang baru dipilih dan belum diunggah. */
export type PickedVideo = { blob: Blob; extension: string; mimeType: string };

export type VideoReading = { kind: 'picked'; video: PickedVideo } | { kind: 'too-large' } | { kind: 'none' };

/** Satu video dari kamera atau galeri; yang melewati [VIDEO_MAX_BYTES] tidak dipakai dan dilaporkan 'too-large'. */
export async function pickVideo(source: 'camera' | 'gallery'): Promise<VideoReading> {
	const [file] = await chooseFile('video/*', { capture: source === 'camera' });
	if (!file) return { kind: 'none' };
	return videoFrom(file);
}

export function videoFrom(file: File): VideoReading {
	if (file.size > VIDEO_MAX_BYTES) return { kind: 'too-large' };
	const mimeType = file.type === 'video/quicktime' || file.type === 'video/webm' ? file.type : 'video/mp4';
	return { kind: 'picked', video: { blob: file, extension: EXTENSIONS[file.type] ?? DEFAULT_EXTENSION, mimeType } };
}
