<script>
  import { attendanceStore, canClockIn, canClockOut, isCompleted } from '../stores/attendance.js';
  import { locationStore, hasLocation } from '../stores/location.js';
  import { userStore, employeeName, departmentName } from '../stores/user.js';

  export let isProcessing = false;
  export let onClockIn = () => {};
  export let onClockOut = () => {};
  export let onNeedLocation = () => {};

  // 當前時間
  let currentTime = '';
  let currentDate = '';

  function updateTime() {
    const now = new Date();
    currentTime = now.toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    currentDate = now.toLocaleDateString('zh-TW', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' });
  }

  updateTime();
  setInterval(updateTime, 1000);

  function handleClick(type) {
    if (!$hasLocation) {
      onNeedLocation();
      return;
    }
    if (type === 'in') {
      onClockIn();
    } else {
      onClockOut();
    }
  }
</script>

<div class="bg-white rounded-2xl shadow-lg overflow-hidden">
  <!-- 用戶資訊區 -->
  <div class="bg-gradient-to-r from-line-green to-emerald-500 text-white p-4">
    <div class="flex items-center gap-3">
      {#if $userStore.employee?.picture_url}
        <img src={$userStore.employee.picture_url} alt="頭像" class="w-12 h-12 rounded-full border-2 border-white/50" />
      {:else}
        <div class="w-12 h-12 rounded-full bg-white/30 flex items-center justify-center">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
        </div>
      {/if}
      <div>
        <p class="font-bold text-lg">{$employeeName || '員工'}</p>
        <p class="text-white/80 text-sm">{$departmentName || '未設定部門'}</p>
      </div>
    </div>
  </div>

  <!-- 時間顯示區 -->
  <div class="p-6 text-center">
    <p class="text-gray-500 text-sm mb-1">{currentDate}</p>
    <p class="text-4xl font-mono font-bold text-gray-800">{currentTime}</p>
  </div>

  <!-- 打卡狀態區 -->
  <div class="px-6 pb-4">
    <div class="flex justify-around text-center">
      <div>
        <p class="text-xs text-gray-400 mb-1">上班時間</p>
        <p class="text-lg font-bold {$attendanceStore.checkInTime ? 'text-line-green' : 'text-gray-300'}">
          {$attendanceStore.checkInTime || '--:--'}
        </p>
      </div>
      <div class="border-l border-gray-200"></div>
      <div>
        <p class="text-xs text-gray-400 mb-1">下班時間</p>
        <p class="text-lg font-bold {$attendanceStore.checkOutTime ? 'text-blue-500' : 'text-gray-300'}">
          {$attendanceStore.checkOutTime || '--:--'}
        </p>
      </div>
    </div>
  </div>

  <!-- 打卡按鈕區 -->
  <div class="p-4 bg-gray-50 border-t border-gray-100">
    {#if $isCompleted}
      <div class="text-center py-4">
        <div class="inline-flex items-center gap-2 text-line-green">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span class="text-xl font-bold">今日打卡完成</span>
        </div>
      </div>
    {:else if $canClockIn}
      <button
        class="w-full py-4 rounded-xl font-bold text-lg text-white transition-all
               {isProcessing || !$hasLocation ? 'bg-gray-300 cursor-not-allowed' : 'bg-line-green hover:bg-line-green-dark active:scale-[0.98]'}"
        onclick={() => handleClick('in')}
        disabled={isProcessing || !$hasLocation}
      >
        {#if isProcessing}
          <span class="inline-flex items-center gap-2">
            <span class="loading-spinner w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
            打卡中...
          </span>
        {:else if !$hasLocation}
          請先取得位置
        {:else}
          上班打卡
        {/if}
      </button>
    {:else if $canClockOut}
      <button
        class="w-full py-4 rounded-xl font-bold text-lg text-white transition-all
               {isProcessing || !$hasLocation ? 'bg-gray-300 cursor-not-allowed' : 'bg-blue-500 hover:bg-blue-600 active:scale-[0.98]'}"
        onclick={() => handleClick('out')}
        disabled={isProcessing || !$hasLocation}
      >
        {#if isProcessing}
          <span class="inline-flex items-center gap-2">
            <span class="loading-spinner w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
            打卡中...
          </span>
        {:else if !$hasLocation}
          請先取得位置
        {:else}
          下班打卡
        {/if}
      </button>
    {/if}
  </div>
</div>

<style>
  .bg-line-green {
    background-color: #06C755;
  }
  .bg-line-green-dark {
    background-color: #05b34c;
  }
  .text-line-green {
    color: #06C755;
  }
  .loading-spinner {
    animation: spin 1s linear infinite;
  }
  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
</style>
