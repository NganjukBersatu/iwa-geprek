import type { AttendanceStatus } from '$lib/api/types';
import type { Tone } from '$lib/components/card/tone';
import { termText } from '$lib/text/terms';
import { attendanceListText } from '$lib/text/attendance-list';

export const STATUS_LABELS: Record<AttendanceStatus, string> = { hadir: attendanceListText.present, telat: attendanceListText.late, izin: attendanceListText.leave, sakit: termText.sick, alfa: termText.absent };

export const STATUS_TONES: Record<AttendanceStatus, Tone> = { hadir: 'success', telat: 'warning', izin: 'info', sakit: 'category', alfa: 'danger' };
