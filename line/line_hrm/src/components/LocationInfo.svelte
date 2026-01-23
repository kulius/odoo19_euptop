<script>
  import { onMount, onDestroy } from 'svelte';
  import { locationStore, hasLocation, formattedCoords } from '../stores/location.js';
  import { geolocationService } from '../services/geolocation.js';

  let isWatching = false;

  onMount(() => {
    startWatching();
  });

  onDestroy(() => {
    stopWatching();
  });

  function startWatching() {
    if (!geolocationService.isSupported()) {
      locationStore.setSupported(false);
      locationStore.setError('您的瀏覽器不支援定位功能');
      return;
    }

    locationStore.startLoading();

    geolocationService.watchPosition(
      (position) => {
        locationStore.setPosition(position);
      },
      (error) => {
        locationStore.setError(error.message);
      }
    );

    isWatching = true;
  }

  function stopWatching() {
    geolocationService.clearWatch();
    isWatching = false;
  }

  function refreshLocation() {
    locationStore.startLoading();
    geolocationService.getCurrentPosition()
      .then(position => {
        locationStore.setPosition(position);
      })
      .catch(error => {
        locationStore.setError(error.message);
      });
  }
</script>

<div class="bg-white rounded-2xl shadow-lg p-4">
  <div class="flex items-center justify-between mb-3">
    <div class="flex items-center gap-2">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
      <span class="text-sm font-medium text-gray-700">GPS 定位</span>
    </div>

    <button
      class="p-2 rounded-lg hover:bg-gray-100 transition-colors"
      onclick={refreshLocation}
      disabled={$locationStore.isLoading}
    >
      <svg xmlns="http://www.w3.org/2000/svg"
           class="h-5 w-5 text-gray-500 {$locationStore.isLoading ? 'animate-spin' : ''}"
           fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
      </svg>
    </button>
  </div>

  {#if $locationStore.isLoading}
    <div class="flex items-center gap-2 text-gray-500">
      <span class="loading-spinner w-4 h-4 border-2 border-line-green border-t-transparent rounded-full"></span>
      <span class="text-sm">正在取得位置...</span>
    </div>
  {:else if $locationStore.error}
    <div class="text-red-500 text-sm flex items-center gap-2">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
      <span>{$locationStore.error}</span>
    </div>
  {:else if $hasLocation}
    <div class="space-y-2">
      <div class="flex items-center gap-2">
        <span class="w-2 h-2 rounded-full bg-line-green animate-pulse"></span>
        <span class="text-sm text-gray-600">已取得位置</span>
      </div>
      <div class="bg-gray-50 rounded-lg p-3">
        <div class="grid grid-cols-2 gap-2 text-xs">
          <div>
            <span class="text-gray-400">緯度</span>
            <p class="font-mono text-gray-700">{$locationStore.current.latitude.toFixed(6)}</p>
          </div>
          <div>
            <span class="text-gray-400">經度</span>
            <p class="font-mono text-gray-700">{$locationStore.current.longitude.toFixed(6)}</p>
          </div>
        </div>
        {#if $locationStore.current.accuracy}
          <div class="mt-2 pt-2 border-t border-gray-200">
            <span class="text-xs text-gray-400">精確度：約 {Math.round($locationStore.current.accuracy)} 公尺</span>
          </div>
        {/if}
      </div>
    </div>
  {:else}
    <div class="text-gray-500 text-sm">尚未取得位置</div>
  {/if}
</div>

<style>
  .bg-line-green {
    background-color: #06C755;
  }
  .loading-spinner {
    animation: spin 1s linear infinite;
  }
  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
</style>
