<script lang="ts">
	import { onMount } from 'svelte';
	import { fetchMetrics, totalNotes } from '$lib/api/metrics';
	import { apiFetch, ApiError } from '$lib/api/client';
	import type { Metrics } from '$lib/types';

	let metrics = $state<Metrics | null>(null);
	let loading = $state(true);
	let error = $state<string | null>(null);

	onMount(init);

	async function init() {
		// La API (is_active) es la autoridad de la sesión: este ping autenticado
		// usa el fetch wrapper común, de modo que un 401 limpia la sesión y
		// redirige a /login. No es un mecanismo de autenticación adicional.
		try {
			await apiFetch('/api/internal/notes-status/');
		} catch (e) {
			if (e instanceof ApiError && e.status === 401) return; // el wrapper ya redirigió
		}
		await load();
	}

	async function load() {
		loading = true;
		error = null;
		try {
			metrics = await fetchMetrics();
		} catch (e) {
			error =
				e instanceof ApiError
					? e.message
					: 'No se pudieron cargar las métricas. Revisa PUBLIC_METRICS_URL.';
		} finally {
			loading = false;
		}
	}

	const total = $derived(metrics ? totalNotes(metrics) : 0);

	const cards = $derived([
		{ label: 'Total de notas', value: total, accent: 'text-slate-900' },
		{ label: 'Pendientes', value: metrics?.pending ?? 0, accent: 'text-amber-600' },
		{ label: 'En curso', value: metrics?.in_progress ?? 0, accent: 'text-blue-600' },
		{ label: 'Hechas', value: metrics?.done ?? 0, accent: 'text-emerald-600' }
	]);
</script>

<div class="mx-auto max-w-5xl p-6">
	<div class="mb-5 flex items-center justify-between">
		<h1 class="text-xl font-semibold">Métricas del tablero</h1>
		<button
			type="button"
			class="rounded border border-slate-300 px-3 py-1 text-sm hover:bg-slate-50 disabled:opacity-50"
			disabled={loading}
			onclick={load}
		>
			{loading ? 'Cargando…' : 'Actualizar'}
		</button>
	</div>

	{#if error}
		<p class="mb-4 rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
			{error}
		</p>
	{/if}

	<div class="grid grid-cols-2 gap-4 lg:grid-cols-4">
		{#each cards as card (card.label)}
			<div class="rounded-lg bg-white p-4 shadow">
				<p class="text-sm text-slate-500">{card.label}</p>
				<p class="mt-1 text-3xl font-bold {card.accent}">
					{loading ? '…' : card.value}
				</p>
			</div>
		{/each}
	</div>

	<p class="mt-6 text-sm text-slate-500">
		Las métricas se consultan desde la URL configurada en
		<code class="rounded bg-slate-200 px-1">PUBLIC_METRICS_URL</code>.
		<a class="text-slate-700 underline hover:text-slate-900" href="/dashboard/board">
			Ir al tablero
		</a>
	</p>
</div>
