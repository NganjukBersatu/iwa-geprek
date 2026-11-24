package id.kongstudio.cafe.feature.printer

/** Halaman uji: [logo] di kepala bila ada, lalu nama slot dan lebar kertas supaya hasilnya bisa dicocokkan dengan printer yang benar. */
internal fun testPageBytes(slotName: String, paper: PaperSize, statement: String, logo: ByteArray? = null): ByteArray {
    val doc = EscPos(paper.columns)
    logo?.let { doc.bytes(it) }
    return doc
        .align(center = true)
        .bold(true)
        .line(slotName)
        .bold(false)
        .line("${paper.millimeters} mm")
        .align()
        .divider()
        .wrapped(statement)
        .divider()
        .cut()
        .build()
}
