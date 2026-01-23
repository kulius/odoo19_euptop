<script>
  import { onMount } from 'svelte';
  import { getAttendanceHistory } from '../services/api.js';
  import { toastStore } from '../stores/toast.js';

  let records = [];
  let isLoading = true;
  let error = null;
  let total = 0;

  onMount(async () => {
    await loadHistory();
  });

  async function loadHistory() {
    isLoading = true;
    error = null;

    try {
      const result = await getAttendanceHistory(30, 0);

      if (result.success) {
        records = result.data.records || [];
        total = result.data.total || 0;
      } else {
        error = result.error?.message || '載入失敗';
        toastStore.error(error);
      }
    } catch (err) {
      error = '載入失敗，請稍後再試';
      toastStore.error(error);
    } finally {
      isLoading = false;
    }
  }

  function formatWorkedHours(hours) {
    if (!hours) return '-';
    const h = Math.floor(hours);
    const m = Math.round((hours - h) * 60);
    return m > 0 ? `${h}小時${m}分` : `${h}小時`;
  }
</script>

<div class="p-4 pb-24">
  {#if isLoading}
    <div class="flex justify-center items-center py-20">
      <div class="w-10 h-10 border-4 border-line-green border-t-transparent rounded-full animate-spin"></div>
    </div>
  {:else if error}
    <div class="bg-red-50 border border-red-200 rounded-xl p-4 text-center">
      <p class="text-red-600">{error}</p>
      <button
        class="mt-3 px-4 py-2 bg-red-500 text-white rounded-lg text-sm font-medium"
        onclick={loadHistory}
      >
        重新載入
      </button>
    </div>
  {:else if records.length === 0}
    <div class="text-center py-20">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-16 w-16 mx-auto text-gray-300 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
      </svg>
      <p class="text-gray-500">目前沒有出勤紀錄</p>
    </div>
  {:else}
    <div class="space-y-3">
      {#each records as record}
        <div class="bg-white rounded-xl shadow-sm overflow-hidden">
          <div class="flex items-center justify-between p-4">
            <div class="flex items-center gap-3">
              <div class="text-center bg-gray-100 rounded-lg px-3 py-2">
                <p class="text-xs text-gray-500">{record.date.slice(5)}</p>
                <p class="text-sm font-bold text-gray-700">週{record.weekday}</p>
              </div>
              <div>
                <div class="flex items-center gap-2 text-sm">
                  <span class="text-line-green font-medium">{record.check_in || '--:--'}</span>
                  <span class="text-gray-400">→</span>
                  <span class="text-blue-500 font-medium">{record.check_out || '--:--'}</span>
                </div>
                {#if record.worked_hours}
                  <p class="text-xs text-gray-400 mt-1">
                    工時：{formatWorkedHours(record.worked_hours)}
                  </p>
                {/if}
              </div>
            </div>

            {#if record.check_out}
              <div class="flex items-center gap-1 text-green-500">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                </svg>
                <span class="text-xs font-medium">完成</span>
              </div>
            {:else if record.check_in}
              <div class="flex items-center gap-1 text-amber-500">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span class="text-xs font-medium">上班中</span>
              </div>
            {/if}
          </div>
        </div>
      {/each}
    </div>

    <p class="text-center text-xs text-gray-400 mt-4">
      共 {total} 筆紀錄
    </p>
  {/if}
</div>

<style>
  .text-line-green {
    color: #06C755;
  }
  .border-line-green {
    border-color: #06C755;
  }
</style>
