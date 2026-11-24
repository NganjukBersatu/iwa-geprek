import { chooseFile } from './photo';
import { PDF_MAX_BYTES } from './upload-limits';

/** Halaman digambar ulang mulai 1,5x ukuran titik PDF (sekitar 108 dpi), lalu diperkecil bertahap sampai muat. */
const START_SCALE = 1.5;
const SCALE_STEP = 0.8;
const MIN_SCALE = 0.25;
const PAGE_JPEG_QUALITY = 0.8;
const PAPER = '#ffffff';
const FALLBACK_NAME = 'lampiran.pdf';

/** PDF hasil pilihan yang sudah muat di [PDF_MAX_BYTES], batas yang dikirim; di atasnya PDF diperkecil otomatis, sehingga pengguna tidak ditolak karena ukuran; [name] adalah nama berkas di perangkat untuk ditampilkan. */
export type PickedPdf = { blob: Blob; name: string };

/** Menggambar ulang setiap halaman sebagai gambar dengan resolusi yang terus diturunkan sampai PDF muat di batas. */
async function shrink(file: Blob): Promise<Blob | null> {
	try {
		const bytes = await file.arrayBuffer();
		const pdfjs = await import('pdfjs-dist');
		const worker = (await import('pdfjs-dist/build/pdf.worker.min.mjs?url')).default;
		pdfjs.GlobalWorkerOptions.workerSrc = worker;
		const { PDFDocument } = await import('pdf-lib');
		const source = await pdfjs.getDocument({ data: new Uint8Array(bytes.slice(0)) }).promise;

		const redraw = async (scale: number): Promise<Blob> => {
			const output = await PDFDocument.create();
			for (let number = 1; number <= source.numPages; number += 1) {
				const page = await source.getPage(number);
				const base = page.getViewport({ scale: 1 });
				const viewport = page.getViewport({ scale });
				const canvas = document.createElement('canvas');
				canvas.width = Math.max(1, Math.floor(viewport.width));
				canvas.height = Math.max(1, Math.floor(viewport.height));
				const context = canvas.getContext('2d');
				if (!context) throw new Error('canvas');
				context.fillStyle = PAPER;
				context.fillRect(0, 0, canvas.width, canvas.height);
				await page.render({ canvasContext: context, viewport }).promise;
				const jpeg = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, 'image/jpeg', PAGE_JPEG_QUALITY));
				if (!jpeg) throw new Error('jpeg');
				const image = await output.embedJpg(await jpeg.arrayBuffer());
				const target = output.addPage([base.width, base.height]);
				target.drawImage(image, { x: 0, y: 0, width: base.width, height: base.height });
			}
			return new Blob([(await output.save()) as BlobPart], { type: 'application/pdf' });
		};

		let scale = START_SCALE;
		let result = await redraw(scale);
		while (result.size > PDF_MAX_BYTES && scale > MIN_SCALE) {
			scale *= SCALE_STEP;
			result = await redraw(scale);
		}
		return result;
	} catch {
		return null;
	}
}

/** Pemilih satu PDF dari perangkat; null bila dibatalkan. */
export async function pickPdf(): Promise<PickedPdf | null> {
	const [file] = await chooseFile('application/pdf');
	if (!file) return null;
	const name = file.name || FALLBACK_NAME;
	if (file.size <= PDF_MAX_BYTES) return { blob: file, name };
	const smaller = await shrink(file);
	return { blob: smaller ?? file, name };
}
