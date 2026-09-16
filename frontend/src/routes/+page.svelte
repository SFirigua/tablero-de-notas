<script lang="ts">
	import { onMount } from 'svelte';
	import { get } from 'svelte/store';
	import { goto } from '$app/navigation';
	import { isAuthenticated } from '$lib/stores/auth';

	onMount(() => {
		void goto(get(isAuthenticated) ? '/dashboard' : '/login');
	});
</script>

<p class="p-6 text-sm text-slate-500">Redirigiendo…</p>
