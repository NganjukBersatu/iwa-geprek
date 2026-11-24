import { bulkApi } from './bulk';
import { del, patch, post, request, toQuery, type SortParam } from './http';
import type { Employee, EmployeeCreate, EmployeePage, EmployeeUpdate } from './types';

const BASE = '/web/management/users';

export type EmployeeParams = SortParam & { search?: string; role_id?: string; outlet_id?: string; active?: boolean; page?: number; size?: number };

export const employeesApi = {
	list: (params: EmployeeParams): Promise<EmployeePage> => request(`${BASE}?${toQuery(params)}`),
	detail: (id: string): Promise<Employee> => request(`${BASE}/${id}`),
	create: (body: EmployeeCreate): Promise<Employee> => post(BASE, body),
	update: (id: string, body: EmployeeUpdate): Promise<Employee> => patch(`${BASE}/${id}`, body),
	remove: (id: string): Promise<void> => del(`${BASE}/${id}`),
	bulk: bulkApi<EmployeeCreate, EmployeeUpdate>(BASE)
};
