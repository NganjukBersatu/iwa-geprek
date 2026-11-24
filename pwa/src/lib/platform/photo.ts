/** Foto untuk unggahan: format apa pun menjadi JPEG, orientasi dibetulkan, sisi terpanjang diperkecil, dan keterangan dicap di bawahnya. */

import { PHOTO_MAX_BYTES } from './upload-limits';

/** Sisi terpanjang hasil konversi; cukup jelas sebagai bukti. */
const MAX_SIDE_PX = 1920;
const JPEG_QUALITY = 0.85;
const MIN_QUALITY = 0.5;
const QUALITY_STEP = 0.1;
const MIN_SIDE_PX = 640;
const SHRINK_FACTOR = 0.8;

// Ukuran cap: satuan dasar untuk foto selebar 720 px, membesar mengikuti lebar foto.
const STAMP_BASE_WIDTH = 720;
const STAMP_PADDING = 12;
const STAMP_LINE_HEIGHT = 21;
const STAMP_TEXT_SIZE = 14;
const STAMP_BOLD_TEXT_SIZE = 16;
const STAMP_BACKGROUND = 'rgb(0 0 0 / 0.902)';
const STAMP_TEXT = '#ffffff';

/** Satu baris cap foto; baris [bold] dicetak tebal dan lebih besar. */
export type StampLine = { text: string; bold?: boolean };

export type PickedPhoto = { blob: Blob };

function canvasOf(width: number, height: number): HTMLCanvasElement {
	const canvas = document.createElement('canvas');
	canvas.width = Math.max(1, Math.round(width));
	canvas.height = Math.max(1, Math.round(height));
	return canvas;
}

function encode(source: CanvasImageSource & { width: number; height: number }, side: number, quality: number): Promise<Blob | null> {
	const scale = Math.min(1, side / Math.max(source.width, source.height));
	const canvas = canvasOf(source.width * scale, source.height * scale);
	const context = canvas.getContext('2d');
	if (!context) return Promise.resolve(null);
	context.drawImage(source, 0, 0, canvas.width, canvas.height);
	return new Promise((resolve) => canvas.toBlob(resolve, 'image/jpeg', quality));
}

/** Menurunkan mutu lalu ukuran sampai di bawah [PHOTO_MAX_BYTES]. */
async function shrinkToLimit(source: CanvasImageSource & { width: number; height: number }): Promise<Blob | null> {
	let side = Math.min(MAX_SIDE_PX, Math.max(source.width, source.height));
	let quality = JPEG_QUALITY;
	for (;;) {
		const blob = await encode(source, side, quality);
		if (!blob) return null;
		if (blob.size <= PHOTO_MAX_BYTES || (side <= MIN_SIDE_PX && quality <= MIN_QUALITY)) return blob;
		if (quality > MIN_QUALITY) quality = Math.max(MIN_QUALITY, quality - QUALITY_STEP);
		else side = Math.floor(side * SHRINK_FACTOR);
	}
}

async function decode(blob: Blob): Promise<ImageBitmap | null> {
	try {
		return await createImageBitmap(blob, { imageOrientation: 'from-image' });
	} catch {
		return null;
	}
}

/** JPEG siap unggah, atau null bila [raw] bukan gambar yang bisa dibaca. */
export async function toUploadJpeg(raw: Blob): Promise<Blob | null> {
	const bitmap = await decode(raw);
	if (!bitmap) return null;
	try {
		return await shrinkToLimit(bitmap);
	} finally {
		bitmap.close();
	}
}

/** Memecah [text] per kata agar setiap potongan muat di [width]. */
function wrap(context: CanvasRenderingContext2D, text: string, width: number): string[] {
	const lines: string[] = [];
	let current = '';
	for (const word of text.split(' ')) {
		const candidate = current === '' ? word : `${current} ${word}`;
		if (current !== '' && context.measureText(candidate).width > width) {
			lines.push(current);
			current = word;
		} else {
			current = candidate;
		}
	}
	if (current !== '') lines.push(current);
	return lines;
}

/** [jpeg] dengan kotak keterangan di bagian bawah foto, tetap dalam batas ukuran unggah; null bila tidak terbaca. */
export async function stampPhoto(jpeg: Blob, lines: readonly StampLine[]): Promise<Blob | null> {
	const bitmap = await decode(jpeg);
	if (!bitmap) return null;
	try {
		const canvas = canvasOf(bitmap.width, bitmap.height);
		const context = canvas.getContext('2d');
		if (!context) return null;
		context.drawImage(bitmap, 0, 0);

		const unit = Math.max(1, canvas.width / STAMP_BASE_WIDTH);
		const padding = STAMP_PADDING * unit;
		const lineHeight = STAMP_LINE_HEIGHT * unit;
		const textWidth = canvas.width - padding * 2;
		const fontOf = (bold: boolean) => `${bold ? 'bold ' : ''}${(bold ? STAMP_BOLD_TEXT_SIZE : STAMP_TEXT_SIZE) * unit}px sans-serif`;

		const wrapped = lines.flatMap((line) => {
			context.font = fontOf(Boolean(line.bold));
			return wrap(context, line.text, textWidth).map((text) => ({ text, bold: Boolean(line.bold) }));
		});
		const boxHeight = wrapped.length * lineHeight + padding * 2;
		const top = canvas.height - boxHeight;
		context.fillStyle = STAMP_BACKGROUND;
		context.fillRect(0, top, canvas.width, boxHeight);
		context.fillStyle = STAMP_TEXT;
		context.textBaseline = 'alphabetic';
		wrapped.forEach((line, index) => {
			context.font = fontOf(line.bold);
			const ascent = context.measureText(line.text).fontBoundingBoxAscent;
			context.fillText(line.text, padding, top + padding + index * lineHeight + ascent);
		});
		return await shrinkToLimit(canvas);
	} finally {
		bitmap.close();
	}
}

/** Membuka pemilih berkas bawaan; null bila pengguna membatalkan. [capture] membuka kamera langsung, tanpa pilihan galeri. */
export function chooseFile(accept: string, options: { capture?: boolean; multiple?: boolean } = {}): Promise<File[]> {
	return new Promise((resolve) => {
		const input = document.createElement('input');
		input.type = 'file';
		input.accept = accept;
		input.multiple = Boolean(options.multiple);
		if (options.capture) input.setAttribute('capture', '');
		input.style.display = 'none';
		const finish = (files: File[]) => {
			input.remove();
			resolve(files);
		};
		input.addEventListener('change', () => finish(Array.from(input.files ?? [])));
		input.addEventListener('cancel', () => finish([]));
		document.body.appendChild(input);
		input.click();
	});
}

/** Hasil memilih foto; 'unreadable' dipisah dari 'cancelled' supaya pengguna diberi tahu bila fotonya tidak bisa dipakai. */
export type PhotoReading = { kind: 'picked'; photo: PickedPhoto } | { kind: 'cancelled' } | { kind: 'unreadable' };

/** Satu foto dari kamera atau galeri, sudah menjadi JPEG siap unggah. */
export async function pickPhoto(source: 'camera' | 'gallery'): Promise<PhotoReading> {
	const [file] = await chooseFile('image/*', { capture: source === 'camera' });
	if (!file) return { kind: 'cancelled' };
	const blob = await toUploadJpeg(file);
	return blob ? { kind: 'picked', photo: { blob } } : { kind: 'unreadable' };
}
