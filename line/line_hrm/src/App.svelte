<script>
  import { onMount } from 'svelte';

  // Services
  import { liffService } from './services/liff.js';
  import { geolocationService } from './services/geolocation.js';
  import { checkBinding, getTodayAttendance, clock, setLineUserId } from './services/api.js';

  // Stores
  import { userStore } from './stores/user.js';
  import { attendanceStore } from './stores/attendance.js';
  import { locationStore } from './stores/location.js';
  import { toastStore } from './stores/toast.js';

  // Components
  import Toast from './components/Toast.svelte';
  import Header from './components/Header.svelte';
  import ClockCard from './components/ClockCard.svelte';
  import LocationInfo from './components/LocationInfo.svelte';
  import BottomMenu from './components/BottomMenu.svelte';

  // Pages
  import BindingPage from './pages/BindingPage.svelte';
  import AttendanceHistory from './pages/AttendanceHistory.svelte';

  // 狀態
  let isInitializing = true;
  let initError = null;
  let isProcessing = false;
  let needsBinding = false;
  let lineProfile = null;

  // 頁面導航
  let currentPage = 'clock';

  // 初始化
  onMount(async () => {
    try {
      const liffOk = await liffService.init();
      if (!liffOk) {
        throw new Error('LIFF 初始化失敗');
      }

      const profile = liffService.getProfile();
      if (!profile) {
        if (!liffService.isLoggedIn()) {
          liffService.login();
        }
        return;
      }

      lineProfile = profile;
      setLineUserId(profile.userId);

      const bindingResult = await checkBinding(profile);
      if (!bindingResult.success) {
        throw new Error('檢查綁定狀態失敗');
      }

      if (!bindingResult.isBound) {
        needsBinding = true;
        isInitializing = false;
        return;
      }

      userStore.setLoggedIn(profile, bindingResult.data);

      // 載入今日出勤狀態
      const attendanceResult = await getTodayAttendance();
      if (attendanceResult.success) {
        attendanceStore.setTodayAttendance(attendanceResult.data);
      }

      if (!geolocationService.isSupported()) {
        locationStore.setSupported(false);
        toastStore.warning('您的裝置不支援定位功能');
      }

      isInitializing = false;
    } catch (error) {
      console.error('Init error:', error);
      initError = error.message;
      isInitializing = false;
    }
  });

  async function handleBindSuccess(userData) {
    userStore.setLoggedIn(lineProfile, userData);

    // 載入今日出勤狀態
    const attendanceResult = await getTodayAttendance();
    if (attendanceResult.success) {
      attendanceStore.setTodayAttendance(attendanceResult.data);
    }

    needsBinding = false;
  }

  async function handleClock(type) {
    if (isProcessing) return;

    const location = $locationStore.current;
    if (!location) {
      toastStore.error('請先取得位置');
      return;
    }

    isProcessing = true;

    try {
      const result = await clock({
        type,
        latitude: location.latitude,
        longitude: location.longitude,
        accuracy: location.accuracy
      });

      if (result.success) {
        if (type === 'in') {
          attendanceStore.setClockIn(result.data);
          toastStore.success(`上班打卡成功 ${result.data.time}`);
        } else {
          attendanceStore.setClockOut(result.data);
          toastStore.success(`下班打卡成功 ${result.data.time}`);
        }

        // 發送 LINE 訊息
        await liffService.sendClockMessage(type, result.data.time);
      } else {
        toastStore.error(result.error?.message || '打卡失敗');
      }
    } catch (error) {
      toastStore.error(error.message || '打卡失敗');
    } finally {
      isProcessing = false;
    }
  }

  function handleClockIn() {
    handleClock('in');
  }

  function handleClockOut() {
    handleClock('out');
  }

  function handleNeedLocation() {
    toastStore.warning('請先允許取得位置');
  }

  function handleNavigate(tabId) {
    currentPage = tabId;
  }

  function goHome() {
    currentPage = 'clock';
  }
</script>

<div class="min-h-screen bg-gray-100 pb-20">
  <Toast />

  {#if isInitializing}
    <div class="min-h-screen flex flex-col items-center justify-center p-4">
      <div class="w-12 h-12 border-4 border-line-green border-t-transparent rounded-full animate-spin"></div>
      <p class="mt-4 text-gray-500">載入中...</p>
    </div>
  {:else if initError}
    <div class="min-h-screen flex flex-col items-center justify-center p-4">
      <div class="bg-red-50 border border-red-200 rounded-lg p-4 max-w-sm">
        <p class="text-red-600 font-bold mb-2">初始化失敗</p>
        <p class="text-red-500 text-sm">{initError}</p>
      </div>
      <button
        class="mt-4 px-6 py-2 bg-line-green text-white rounded-lg font-bold"
        onclick={() => window.location.reload()}
      >
        重新載入
      </button>
    </div>
  {:else if needsBinding}
    <BindingPage {lineProfile} onBindSuccess={handleBindSuccess} />
  {:else}
    {#if currentPage === 'clock'}
      <Header title="LINE 打卡系統" />
      <main class="container mx-auto px-4 py-4 space-y-4 max-w-lg">
        <ClockCard
          {isProcessing}
          onClockIn={handleClockIn}
          onClockOut={handleClockOut}
          onNeedLocation={handleNeedLocation}
        />
        <LocationInfo />
      </main>
    {:else if currentPage === 'history'}
      <Header title="出勤紀錄" showBack={true} onBack={goHome} />
      <AttendanceHistory />
    {/if}

    <BottomMenu activeTab={currentPage} onNavigate={handleNavigate} />
  {/if}
</div>

<style>
  .bg-line-green {
    background-color: #06C755;
  }
  .border-line-green {
    border-color: #06C755;
  }
</style>
