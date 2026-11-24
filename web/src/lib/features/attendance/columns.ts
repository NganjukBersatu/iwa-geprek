import { controlText } from '$lib/text/controls';
import { QUIET_VALUE } from "$lib/components/table/quiet-value";
import type { RecapDay, RecapOvertime, UserRecap } from "$lib/api/types";
import type { Column } from "$lib/components/table/types";
import { EMPTY_VALUE, formatNumber, formatRupiah } from "$lib/format/currency";
import { formatDateTime, formatDuration } from "$lib/format/datetime";
import { dayLabel, formatDayMonth } from "$lib/date/range";
import { STATUS_LABELS } from "../attendance-list/labels";
import { userName } from "./names";
import { termText } from '$lib/text/terms';
import { attendanceReportText } from '$lib/text/attendance-report';
import { format } from '$lib/text/format';

const zero = (value: number, active: string) =>
  value > 0 ? active : QUIET_VALUE;
const count = (value: number) => formatNumber(value, 0);

export const attendanceColumns: Column<UserRecap>[] = [
  {
    key: "nama",
    label: termText.employee,
    align: "left",
    value: userName,
    sort: "user",
  },
  {
    key: "jadwal",
    label: termText.schedule,
    value: (row) => count(row.scheduled),
    class: () => "text-slate-500",
    sort: "scheduled",
  },
  {
    key: "hadir",
    label: attendanceReportText.present,
    value: (row) => count(row.present),
    class: () => "font-semibold text-success-700",
    sort: "present",
  },
  {
    key: "telat",
    label: attendanceReportText.late,
    value: (row) => count(row.late),
    class: (row) => `font-semibold ${zero(row.late, "text-warning-700")}`,
    sort: "late",
  },
  {
    key: "izin",
    label: attendanceReportText.leave,
    value: (row) => count(row.leave),
    class: (row) => zero(row.leave, "text-info-700"),
    sort: "leave",
  },
  {
    key: "sakit",
    label: termText.sick,
    value: (row) => count(row.sick),
    class: (row) => zero(row.sick, "text-category-700"),
    sort: "sick",
  },
  {
    key: "alfa",
    label: termText.absent,
    value: (row) =>
      row.automatic_absences > 0
        ? format(attendanceReportText.absentWithAutomatic, { count: count(row.absent), automatic: count(row.automatic_absences) })
        : count(row.absent),
    class: (row) => `font-semibold ${zero(row.absent, "text-danger-700")}`,
    sort: "absent",
  },
  {
    key: "kerja",
    label: attendanceReportText.workHoursTitle,
    value: (row) => formatDuration(row.work_minutes),
    sort: "work_minutes",
  },
  {
    key: "menit_telat",
    label: attendanceReportText.lateMinutes,
    value: (row) => count(row.late_minutes),
    class: (row) => zero(row.late_minutes, "text-warning-700"),
    sort: "late_minutes",
  },
  {
    key: "potongan",
    label: termText.discount,
    value: (row) => formatRupiah(row.penalty),
    class: (row) => `font-semibold ${zero(row.penalty, "text-danger-700")}`,
    sort: "penalty",
  },
  {
    key: "lembur",
    label: attendanceReportText.overtime,
    value: (row) =>
      row.overtime_minutes > 0
        ? formatDuration(row.overtime_minutes)
        : EMPTY_VALUE,
    class: (row) =>
      `font-semibold ${zero(row.overtime_minutes, "text-category-700")}`,
    sort: "overtime_minutes",
  },
];

const day = (iso: string) => `${dayLabel(iso).weekday} ${formatDayMonth(iso)}`;
const time = (iso: string | null) => (iso ? formatDateTime(iso) : EMPTY_VALUE);

export const dayColumns: Column<RecapDay>[] = [
  {
    key: "tanggal",
    label: termText.date,
    align: "left",
    value: (row) => day(row.date),
    sort: "date",
  },
  {
    key: "kode",
    label: termText.code,
    align: "left",
    value: (row) => row.code ?? EMPTY_VALUE,
    sort: "code",
  },
  {
    key: "status",
    label: termText.status,
    align: "left",
    value: (row) => STATUS_LABELS[row.status],
    sort: "status",
  },
  {
    key: "masuk",
    label: attendanceReportText.clockedIn,
    align: "left",
    value: (row) => time(row.clock_in_at),
    sort: "clock_in",
  },
  {
    key: "pulang",
    label: attendanceReportText.clockedOut,
    align: "left",
    value: (row) => time(row.clock_out_at),
    sort: "clock_out",
  },
  {
    key: "kerja",
    label: attendanceReportText.workHours,
    value: (row) => formatDuration(row.work_minutes),
    sort: "work_minutes",
  },
  {
    key: "telat",
    label: attendanceReportText.late,
    value: (row) =>
      row.late_minutes > 0 ? format(controlText.minutesCount, { count: row.late_minutes }) : EMPTY_VALUE,
    class: (row) =>
      row.late_minutes > 0 ? "text-warning-700" : QUIET_VALUE,
    sort: "late_minutes",
  },
  {
    key: "potongan",
    label: termText.discount,
    value: (row) => (row.penalty > 0 ? formatRupiah(row.penalty) : EMPTY_VALUE),
    class: (row) =>
      row.penalty > 0 ? "font-semibold text-danger-700" : QUIET_VALUE,
    sort: "penalty",
  },
  {
    key: "catatan",
    label: termText.note,
    align: "left",
    value: (row) => row.note ?? "",
    sort: "note",
  },
];

export const overtimeColumns: Column<RecapOvertime>[] = [
  {
    key: "tanggal",
    label: termText.date,
    align: "left",
    value: (row) => day(row.date),
    sort: "date",
  },
  {
    key: "jenis",
    label: termText.kind,
    align: "left",
    value: (row) => (row.scheduled ? attendanceReportText.scheduled : attendanceReportText.unscheduled),
    sort: "kind",
  },
  {
    key: "mulai",
    label: attendanceReportText.started,
    align: "left",
    value: (row) => time(row.start_at),
    sort: "start",
  },
  {
    key: "selesai",
    label: attendanceReportText.finished,
    align: "left",
    value: (row) => time(row.end_at),
    sort: "end",
  },
  {
    key: "durasi",
    label: attendanceReportText.duration,
    value: (row) => formatDuration(row.minutes),
    class: () => "font-semibold",
    sort: "minutes",
  },
  {
    key: "catatan",
    label: termText.note,
    align: "left",
    value: (row) => row.note ?? "",
    sort: "note",
  },
];
