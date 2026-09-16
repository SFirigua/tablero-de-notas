<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		title: string;
		open: boolean;
		onclose: () => void;
		children: Snippet;
	}

	let { title, open, onclose, children }: Props = $props();

	let dialogEl = $state<HTMLDialogElement | null>(null);

	$effect(() => {
		if (!dialogEl) return;
		if (open && !dialogEl.open) dialogEl.showModal();
		if (!open && dialogEl.open) dialogEl.close();
	});

	function handleBackdropClick(event: MouseEvent) {
		if (event.target === dialogEl) onclose();
	}
</script>

<dialog
	bind:this={dialogEl}
	class="w-full max-w-md rounded-lg p-0 shadow-xl backdrop:bg-slate-900/40"
	aria-label={title}
	onclick={handleBackdropClick}
	oncancel={(event) => {
		event.preventDefault();
		onclose();
	}}
>
	<div class="p-6">
		<div class="mb-4 flex items-center justify-between">
			<h2 class="text-lg font-semibold">{title}</h2>
			<button
				type="button"
				class="rounded px-1 text-slate-400 hover:text-slate-700"
				aria-label="Cerrar"
				onclick={onclose}
			>
				✕
			</button>
		</div>
		{@render children()}
	</div>
</dialog>
