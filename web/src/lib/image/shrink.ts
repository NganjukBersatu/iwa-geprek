const MAX_SIDE = 800;
/** Large enough for small print to stay readable when the server reads the text. */
export const READING_MAX_SIDE = 2000;
const JPEG_QUALITY = 0.85;

/** Scales a picture down to at most maxSide px on its longest side as a JPEG; null when the browser cannot read it. */
export async function shrinkImage(file: File, maxSide = MAX_SIDE): Promise<Blob | null> {
	try {
		const bitmap = await createImageBitmap(file);
		const scale = Math.min(1, maxSide / Math.max(bitmap.width, bitmap.height));
		const width = Math.max(1, Math.round(bitmap.width * scale));
		const height = Math.max(1, Math.round(bitmap.height * scale));
		const canvas = document.createElement('canvas');
		canvas.width = width;
		canvas.height = height;
		const context = canvas.getContext('2d');
		if (!context) return null;
		context.fillStyle = '#ffffff';
		context.fillRect(0, 0, width, height);
		context.drawImage(bitmap, 0, 0, width, height);
		bitmap.close();
		return await new Promise<Blob | null>((done) => canvas.toBlob(done, 'image/jpeg', JPEG_QUALITY));
	} catch {
		return null;
	}
}

export async function preparePhoto(file: File, maxSide = MAX_SIDE): Promise<File> {
	if (!file.type.startsWith('image/')) return file;
	const small = await shrinkImage(file, maxSide);
	if (!small) return file;
	return new File([small], `${file.name.replace(/\.[^.]*$/, '')}.jpg`, { type: 'image/jpeg' });
}
