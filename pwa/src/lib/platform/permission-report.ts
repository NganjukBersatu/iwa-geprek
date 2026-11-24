import { ApiCaller } from '$lib/api/http';

const REPORT_PATH = '/v2/client-events/permission-failures';

export type PermissionFailureReport = { kind: string; reason: string; elapsedMillis: number; reference: string };

/** Melapor kegagalan izin ke server agar terlihat di log; gagal melapor tidak pernah mengganggu pengguna. */
export async function reportPermissionFailure(report: PermissionFailureReport): Promise<void> {
	const reason = report.reason === 'serviceOff' ? 'service_off' : report.reason;
	try {
		await new ApiCaller().write('POST', REPORT_PATH, { kind: report.kind, reason, elapsed_millis: report.elapsedMillis, reference: report.reference });
	} catch {
		// Laporan hanya pelengkap diagnosis.
	}
}
