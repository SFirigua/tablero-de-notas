<script lang="ts">
	import { onMount } from 'svelte';
	import { get } from 'svelte/store';
	import { goto } from '$app/navigation';
	import { login } from '$lib/api/auth';
	import { ApiError } from '$lib/api/client';
	import { isAuthenticated, setSession } from '$lib/stores/auth';

	let email = $state('');
	let password = $state('');
	let error = $state<string | null>(null);
	let loading = $state(false);

	onMount(() => {
		if (get(isAuthenticated)) void goto('/dashboard');
	});

	function quickAccess(demoEmail: string, demoPassword: string) {
		email = demoEmail;
		password = demoPassword;
		error = null;
	}

	async function submit(event: SubmitEvent) {
		event.preventDefault();
		error = null;
		loading = true;
		try {
			const data = await login(email, password);
			setSession(data.access, data.user);
			await goto('/dashboard');
		} catch (e) {
			if (e instanceof ApiError && e.status === 401) {
				error = 'Credenciales inválidas o usuario inactivo.';
			} else {
				error = e instanceof ApiError ? e.message : 'No se pudo iniciar sesión.';
			}
		} finally {
			loading = false;
		}
	}
</script>

<div class="mx-auto mt-24 max-w-sm rounded-lg bg-white p-6 shadow">
	<h1 class="mb-1 text-lg font-semibold">Tablero de Notas</h1>
	<p class="mb-5 text-sm text-slate-500">Inicia sesión para continuar</p>

	<form class="flex flex-col gap-3" onsubmit={submit}>
		<input
			class="rounded border border-slate-300 px-3 py-2"
			type="email"
			placeholder="Email"
			bind:value={email}
			required
			autocomplete="email"
		/>
		<input
			class="rounded border border-slate-300 px-3 py-2"
			type="password"
			placeholder="Contraseña"
			bind:value={password}
			required
			autocomplete="current-password"
		/>
		{#if error}
			<p class="text-sm text-red-600">{error}</p>
		{/if}
		<button
			class="rounded bg-slate-900 px-3 py-2 font-medium text-white hover:bg-slate-700 disabled:opacity-50"
			type="submit"
			disabled={loading}
		>
			{loading ? 'Entrando…' : 'Entrar'}
		</button>
	</form>

	<div class="mt-5 border-t border-slate-200 pt-4">
		<p class="mb-2 text-xs font-medium uppercase tracking-wide text-slate-400">
			Acceso rápido
		</p>
		<div class="grid grid-cols-2 gap-2">
			<button
				type="button"
				class="rounded border border-slate-300 px-3 py-2 text-left text-sm hover:bg-slate-50"
				onclick={() => quickAccess('admin@ejemplo.com', 'Admin123!')}
			>
				<span class="block font-medium">Admin Demo</span>
				<span class="block text-xs text-slate-500">admin@ejemplo.com</span>
			</button>
			<button
				type="button"
				class="rounded border border-slate-300 px-3 py-2 text-left text-sm hover:bg-slate-50"
				onclick={() => quickAccess('user@ejemplo.com', 'User123!')}
			>
				<span class="block font-medium">User Demo</span>
				<span class="block text-xs text-slate-500">user@ejemplo.com</span>
			</button>
		</div>
	</div>
</div>
