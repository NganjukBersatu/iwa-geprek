package id.kongstudio.cafe.ui.component.moneyfield

import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.OffsetMapping
import androidx.compose.ui.text.input.TransformedText
import androidx.compose.ui.text.input.VisualTransformation
import id.kongstudio.cafe.ui.component.textfield.AppTextField

private const val Prefix = "Rp "
private const val GroupSize = 3
private const val Separator = '.'

/** Kolom rupiah yang menyimpan angkanya saja ([amount], null bila kosong) dan menampilkan "Rp 50.000", dengan karakter selain angka diabaikan agar tempelan "50.000" tetap terbaca. */
@Composable
fun MoneyField(
    amount: Long?,
    onAmountChange: (Long?) -> Unit,
    label: String,
    modifier: Modifier = Modifier,
    isError: Boolean = false,
) {
    AppTextField(
        value = amount?.toString().orEmpty(),
        onValueChange = { text -> onAmountChange(amountOf(text)) },
        label = label,
        modifier = modifier,
        isError = isError,
        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
        visualTransformation = RupiahTransformation,
    )
}

/** Kolom rupiah untuk layar yang menyimpan angkanya sebagai teks angka ([value], kosong bila belum diisi). */
@Composable
fun MoneyField(
    value: String,
    onValueChange: (String) -> Unit,
    label: String,
    modifier: Modifier = Modifier,
    isError: Boolean = false,
) {
    MoneyField(
        amount = value.toLongOrNull(),
        onAmountChange = { onValueChange(it?.toString().orEmpty()) },
        label = label,
        modifier = modifier,
        isError = isError,
    )
}

/** Angka dari ketikan atau tempelan: nol di depan dibuang, tetapi satu nol tetap dipertahankan supaya nominal 0 bisa diisi. */
private fun digitsOf(text: String): String {
    val digits = text.filter { it.isDigit() }.take(MaxDigits)
    return digits.trimStart('0').ifEmpty { if (digits.isEmpty()) "" else "0" }
}

// Lebih dari ini sudah bukan uang kasir, dan menjaga Long tidak meluap.
private const val MaxDigits = 12

/** Angka dari ketikan; kosong berarti belum diisi, sedangkan "0" tetap nol karena Rp 0 adalah jumlah yang sah (laci kosong, ekstra gratis). */
private fun amountOf(text: String): Long? {
    val digits = text.filter { it.isDigit() }
    if (digits.isEmpty()) return null
    return digits.trimStart('0').ifEmpty { "0" }.take(MaxDigits).toLong()
}

/** "50000" tampil "Rp 50.000"; kursor tetap di antara angka yang sama. */
private object RupiahTransformation : VisualTransformation {
    override fun filter(text: AnnotatedString): TransformedText {
        val digits = text.text
        if (digits.isEmpty()) return TransformedText(text, OffsetMapping.Identity)
        val grouped = digits.reversed().chunked(GroupSize).joinToString(Separator.toString()).reversed()
        val shown = Prefix + grouped

        val mapping = object : OffsetMapping {
            override fun originalToTransformed(offset: Int): Int {
                // Pemisah di depan angka ke-[offset]: satu per kelompok tiga yang sudah dilewati, dihitung dari kanan.
                val separatorsBefore = (digits.length - 1) / GroupSize - (digits.length - offset) / GroupSize
                return Prefix.length + offset + separatorsBefore.coerceAtLeast(0)
            }

            override fun transformedToOriginal(offset: Int): Int {
                val inGroups = (offset - Prefix.length).coerceIn(0, grouped.length)
                return grouped.take(inGroups).count { it != Separator }
            }
        }
        return TransformedText(AnnotatedString(shown), mapping)
    }
}
