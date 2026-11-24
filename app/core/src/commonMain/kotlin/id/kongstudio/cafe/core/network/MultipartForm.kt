package id.kongstudio.cafe.core.network

import io.ktor.client.request.HttpRequestBuilder
import io.ktor.client.request.forms.FormBuilder
import io.ktor.client.request.forms.MultiPartFormDataContent
import io.ktor.client.request.forms.formData
import io.ktor.client.request.setBody
import io.ktor.http.Headers
import io.ktor.http.HttpHeaders

/** Mengirim isian multipart; berkas dilampirkan dengan [appendFile]. */
fun HttpRequestBuilder.multipart(build: FormBuilder.() -> Unit) {
    setBody(MultiPartFormDataContent(formData(build)))
}

fun FormBuilder.appendFile(name: String, bytes: ByteArray, mimeType: String, fileName: String) {
    append(
        name,
        bytes,
        Headers.build {
            append(HttpHeaders.ContentType, mimeType)
            append(HttpHeaders.ContentDisposition, "filename=\"$fileName\"")
        },
    )
}
