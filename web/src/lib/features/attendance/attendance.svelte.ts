import { api } from "$lib/api";
import type { AttendanceRecap } from "$lib/api/types";
import { createReportFilters } from "../report/filters";
import {
  rangeParams,
  ReportState,
  type ReportQuery,
} from "../report/report.svelte";
import { ListSort, sortKeys } from "$lib/components/table/list-sort.svelte";
import { attendanceColumns, dayColumns, overtimeColumns } from "./columns";

export class AttendanceState extends ReportState<ReportQuery, AttendanceRecap> {
  override readonly tables = [
    "attendance_records",
    "schedules",
    "shift_codes",
    "overtime_records",
  ];

  readonly sort = new ListSort(
    "rekap-absen",
    sortKeys(attendanceColumns),
    () => void this.queryChanged(this.query),
  );
  readonly daySort = new ListSort(
    "rekap-absen-hari",
    sortKeys(dayColumns),
    () => void this.queryChanged(this.query),
  );
  readonly overtimeSort = new ListSort(
    "rekap-absen-lembur",
    sortKeys(overtimeColumns),
    () => void this.queryChanged(this.query),
  );

  filters = createReportFilters();

  get query(): ReportQuery {
    return {
      branch: this.filters.get("cabang"),
      range: this.filters.range("rentang"),
    };
  }

  protected fetch(query: ReportQuery): Promise<AttendanceRecap> {
    return api.reports.attendance({
      ...rangeParams(query.range),
      sort: this.sort.param,
      day_sort: this.daySort.param,
      overtime_sort: this.overtimeSort.param,
    });
  }
}
