<script lang="ts">
	import '../app.css';

	let { children } = $props();
</script>

<div class="flex min-h-screen flex-col">
	<header class="bg-slate-900 px-6 py-4 text-lg font-semibold text-white shadow">
		Tablero de Notas
	</header>

	<main class="flex-1">
		{@render children()}
	</main>
</div>
