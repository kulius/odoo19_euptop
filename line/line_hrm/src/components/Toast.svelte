<script>
  import { toastStore } from '../stores/toast.js';

  const typeStyles = {
    success: 'bg-green-500',
    error: 'bg-red-500',
    warning: 'bg-amber-500',
    info: 'bg-blue-500'
  };

  const typeIcons = {
    success: '✓',
    error: '✕',
    warning: '⚠',
    info: 'ℹ'
  };
</script>

{#if $toastStore.show}
  <div class="fixed top-16 left-0 right-0 z-50 flex justify-center px-4 animate-slide-down">
    <div class="{typeStyles[$toastStore.type]} text-white px-4 py-3 rounded-lg shadow-lg flex items-center gap-2 max-w-sm">
      <span class="text-lg">{typeIcons[$toastStore.type]}</span>
      <span class="text-sm font-medium">{$toastStore.message}</span>
    </div>
  </div>
{/if}

<style>
  @keyframes slide-down {
    from {
      opacity: 0;
      transform: translateY(-20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .animate-slide-down {
    animation: slide-down 0.3s ease-out;
  }
</style>
