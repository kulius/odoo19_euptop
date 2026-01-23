<script>
  export let activeTab = 'clock';
  export let onNavigate = (tab) => {};

  const tabs = [
    { id: 'clock', label: '打卡', icon: 'clock' },
    { id: 'history', label: '紀錄', icon: 'history' },
  ];

  function handleClick(tabId) {
    onNavigate(tabId);
  }
</script>

<nav class="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 safe-area-bottom">
  <div class="max-w-lg mx-auto px-4">
    <div class="flex justify-around py-2">
      {#each tabs as tab}
        <button
          class="flex flex-col items-center py-2 px-6 rounded-lg transition-colors
                 {activeTab === tab.id ? 'text-line-green' : 'text-gray-400 hover:text-gray-600'}"
          onclick={() => handleClick(tab.id)}
        >
          {#if tab.icon === 'clock'}
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          {:else if tab.icon === 'history'}
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
          {/if}
          <span class="text-xs mt-1 font-medium">{tab.label}</span>
        </button>
      {/each}
    </div>
  </div>
</nav>

<style>
  .text-line-green {
    color: #06C755;
  }
  .safe-area-bottom {
    padding-bottom: env(safe-area-inset-bottom, 0);
  }
</style>
