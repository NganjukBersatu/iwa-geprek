import { toast } from '$lib/components/feedback/toast.svelte';
import { api } from '$lib/api';
import type { PaymentMethod } from '$lib/api/types';
import { Filters } from '$lib/components/filter/filters.svelte';
import { ListSort, sortKeys } from '$lib/components/table/list-sort.svelte';
import { ManageState } from '../manage/manage.svelte';
import { paymentMethodColumns } from './columns';
import { BRANCH_SORT } from '$lib/components/table/branch-column';
import { branchList } from '$lib/stores/branch';
import { termText } from '$lib/text/terms';
import { paymentMethodText } from '$lib/text/payment-methods';


/** The icons the server accepts, with the words the admin picks them by. */
export const PAYMENT_ICONS = [
	{ value: 'ti-cash', label: paymentMethodText.kindCash },
	{ value: 'ti-qrcode', label: paymentMethodText.kindQr },
	{ value: 'ti-credit-card', label: paymentMethodText.kindCard },
	{ value: 'ti-building-bank', label: paymentMethodText.kindBank },
	{ value: 'ti-device-mobile', label: paymentMethodText.kindEwallet },
	{ value: 'ti-wallet', label: paymentMethodText.kindWallet },
	{ value: 'ti-receipt', label: paymentMethodText.kindCredit },
	{ value: 'ti-gift', label: paymentMethodText.kindVoucher }
];

/** Payment methods are kept per branch; the list shows one branch, or every branch while none is picked. */
export class PaymentMethodsState extends ManageState<PaymentMethod> {
	override readonly tables = ['payment_methods'];
	readonly sort = new ListSort('metode-bayar', [...sortKeys(paymentMethodColumns), BRANCH_SORT], () => void this.queryChanged());

	readonly filters = new Filters([{ kind: 'select', key: 'cabang', label: termText.branch, options: [] }]);

	get query(): string | null {
		return this.filters.get('cabang');
	}

	protected async fetch(): Promise<void> {
		const outlets = await branchList();
		this.filters.setOptions('cabang', outlets.map((outlet) => ({ value: outlet.id, label: outlet.name })));
		this.items = await api.paymentMethods.list(this.sort.param);
		this.total = this.items.length;
	}

	protected label(method: PaymentMethod): string {
		return method.label;
	}

	private announce(text: string): void {
		toast.show(text);
	}

	closeDialogs(): void {
		this.actionError = '';
	}

}
