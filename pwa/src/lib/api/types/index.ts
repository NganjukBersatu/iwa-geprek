import type { Schemas } from '../contract';

export type SessionOut = Schemas['BrowserSessionOut'];
export type UserOut = SessionOut['user'];

export type AttendanceStateDto = Schemas['AttendanceStateOut'];
export type AttendanceDto = Schemas['EmployeeAttendanceOut'];
export type BranchDto = Schemas['AttendanceBranchOut'];
export type ScheduleSummaryDto = Schemas['ScheduleSummary'];
export type DayPlanDto = Schemas['DayPlanOut'];
export type SegmentDto = Schemas['SegmentOut'];
export type SelfScheduleOptionsDto = Schemas['SelfScheduleOptionsOut'];
export type SuggestionDto = Schemas['SuggestionOut'];
export type ChoiceDto = Schemas['ChoiceOut'];
export type SelfScheduleInDto = Schemas['SelfScheduleIn'];
export type SummaryDto = Schemas['AttendanceSummaryOut'];
