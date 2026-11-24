import { del, inBranch, patch, post, request, toQuery, upload } from './http';
import type { PaymentMethod, PaymentMethodCreate, PaymentMethodUpdate } from './types';

const BASE = '/web/management/payment-methods';

export const paymentMethodsApi = {
	list: (sort?: string): Promise<PaymentMethod[]> => request(`${BASE}?${toQuery({ sort })}`),
	detail: (id: string): Promise<PaymentMethod> => request(`${BASE}/${id}`),
	create: (outletId: string, body: PaymentMethodCreate): Promise<PaymentMethod> => post(inBranch(BASE, outletId), body),
	update: (method: PaymentMethod, body: PaymentMethodUpdate): Promise<PaymentMethod> => patch(inBranch(`${BASE}/${method.id}`, method.outlet_id), body),
	remove: (method: PaymentMethod): Promise<void> => del(inBranch(`${BASE}/${method.id}`, method.outlet_id)),
	uploadImage: (method: PaymentMethod, file: Blob): Promise<PaymentMethod> => upload(inBranch(`${BASE}/${method.id}/image`, method.outlet_id), 'file', file),
	removeImage: (method: PaymentMethod): Promise<PaymentMethod> => request(inBranch(`${BASE}/${method.id}/image`, method.outlet_id), { method: 'DELETE' })
};
