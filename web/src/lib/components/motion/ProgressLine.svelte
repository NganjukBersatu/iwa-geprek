<script lang="ts">
	import { controlText } from '$lib/text/controls';
</script>

<!-- Garis progres tanpa persen; pemanggil menumpuknya di atas isi (induk relative) supaya tata letak tidak bergeser. -->
<div class="progress-line" role="status" aria-label={controlText.loading}></div>
