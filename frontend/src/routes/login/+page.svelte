<script lang="ts">
	import { onMount } from 'svelte';
	import { get } from 'svelte/store';
	import { goto } from '$app/navigation';
	import { login } from '$lib/api/auth';
	import { ApiError } from '$lib/api/client';
	import { isAuthenticated, setSession } from '$lib/stores/auth';

	let email = $state('');
	let password = $state('');
	let showPassword = $state(false);
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

<div class="anim-rise-in mx-auto mt-24 max-w-sm rounded-lg bg-white p-6 shadow">
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
		<div class="relative">
			<input
				class="w-full rounded border border-slate-300 px-3 py-2 pr-10"
				type={showPassword ? 'text' : 'password'}
				placeholder="Contraseña"
				bind:value={password}
				required
				autocomplete="current-password"
			/>
			<button
				type="button"
				class="absolute inset-y-0 right-0 flex items-center px-3 text-slate-400 hover:text-slate-600"
				aria-label={showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
				title={showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
				onclick={() => (showPassword = !showPassword)}
			>
				{#if showPassword}
					<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"
						stroke-width="1.5" stroke="currentColor" class="h-5 w-5" aria-hidden="true">
						<path stroke-linecap="round" stroke-linejoin="round"
							d="M3.98 8.223A10.477 10.477 0 0 0 1.934 12C3.226 16.338 7.244 19.5 12 19.5q1.494 0 2.863-.395m-8.635-12.877A10.45 10.45 0 0 1 12 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 0 1-4.293 5.774M6.228 6.228 3 3m3.228 3.228 3.65 3.65m7.894 7.894L21 21m-3.228-3.228-3.65-3.65m0 0a3 3 0 1 0-4.243-4.243m4.242 4.242L9.88 9.88" />
					</svg>
				{:else}
					<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"
						stroke-width="1.5" stroke="currentColor" class="h-5 w-5" aria-hidden="true">
						<path stroke-linecap="round" stroke-linejoin="round"
							d="M2.036 12.322a1.012 1.012 0 0 1 0-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178Z" />
						<path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
					</svg>
				{/if}
			</button>
		</div>
		{#if error}
			<p class="text-sm text-red-600">{error}</p>
		{/if}
		<button
			class="rounded bg-slate-900 px-3 py-2 font-medium text-white transition hover:bg-slate-700 active:scale-[0.99] disabled:opacity-50"
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
