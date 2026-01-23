<script>
  export let title = '打卡系統';
  export let showBack = false;
  export let onBack = null;
</script>

<header class="bg-line-green text-white px-4 py-3 sticky top-0 z-50 shadow-md">
  <div class="flex items-center justify-between max-w-lg mx-auto">
    {#if showBack && onBack}
      <button
        class="p-1 -ml-1 rounded-full hover:bg-white/20 transition-colors"
        onclick={onBack}
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
      </button>
    {:else}
      <div class="w-8"></div>
    {/if}

    <h1 class="text-lg font-bold">{title}</h1>

    <div class="w-8"></div>
  </div>
</header>

<style>
  .bg-line-green {
    background-color: #06C755;
  }
</style>
