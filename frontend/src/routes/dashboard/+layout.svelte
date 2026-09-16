<script lang="ts">
	import { onMount } from 'svelte';
	import { get } from 'svelte/store';
	import { goto } from '$app/navigation';
	import { logout } from '$lib/api/auth';
	import { clearSession, currentUser, isAuthenticated, isAdmin } from '$lib/stores/auth';

	let { children } = $props();

	onMount(() => {
		if (!get(isAuthenticated)) void goto('/login');
	});

	async function handleLogout() {
		await logout().catch(() => undefined);
		clearSession();
		await goto('/login');
	}
</script>

<div class="flex h-screen flex-col">
	<header class="flex flex-wrap items-center justify-between gap-3 bg-slate-900 px-6 py-3 text-white">
		<div class="flex items-center gap-6">
			<span class="text-base font-semibold">Tablero de Notas</span>
			<nav class="flex items-center gap-4 text-sm">
				<a class="hover:text-slate-300" href="/dashboard">Métricas</a>
				<a class="hover:text-slate-300" href="/dashboard/board">Tablero</a>
				{#if $isAdmin}
					<a class="hover:text-slate-300" href="/dashboard/users">Usuarios</a>
				{/if}
			</nav>
		</div>
		<div class="flex items-center gap-4 text-sm">
			{#if $currentUser}
				<span class="text-slate-300">
					{$currentUser.name} · {$currentUser.role}
				</span>
			{/if}
			<button
				type="button"
				class="rounded border border-slate-600 px-3 py-1 hover:bg-slate-700"
				onclick={handleLogout}
			>
				Cerrar sesión
			</button>
		</div>
	</header>

	<main class="min-h-0 flex-1">
		{@render children()}
	</main>
</div>
