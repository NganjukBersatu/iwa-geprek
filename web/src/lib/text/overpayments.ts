/** The sentences of the report of payments above the total of the order. */
export const overpaymentText = {
	valid: 'Sah',
	receipt: 'Nota',
	orderTotal: 'Total Pesanan',
	received: 'Diterima',
	excess: 'Kelebihan',
	summaryCaption: 'Pembayaran non-tunai melebihi total pesanan',
	totalExcess: 'Total kelebihan',
	totalCaption: 'Termasuk transaksi yang kemudian dibatalkan',
	listTitle: 'Daftar kelebihan pembayaran',
	listDescription: 'Kelebihan = diterima − total pesanan',
	noOverpayments: 'Tidak ada kelebihan pembayaran di periode ini.'
} as const;
