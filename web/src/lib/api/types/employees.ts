import type { Schemas } from '../contract';

export type Employee = Schemas['UserOut'];
export type EmployeeCreate = Schemas['UserCreateIn'];
export type EmployeeUpdate = Schemas['UserUpdateIn'];
export type EmployeePage = Schemas['UserPageOut'];
