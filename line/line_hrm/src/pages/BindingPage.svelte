<script>
  import { toastStore } from '../stores/toast.js';
  import { bindEmployee } from '../services/api.js';

  export let lineProfile = null;
  export let onBindSuccess = (data) => {};

  let employeeName = '';
  let isLoading = false;
  let errorMessage = '';

  async function handleSubmit() {
    if (!employeeName.trim()) {
      errorMessage = '請輸入姓名';
      return;
    }

    if (employeeName.trim().length < 2) {
      errorMessage = '姓名至少需要 2 個字';
      return;
    }

    errorMessage = '';
    isLoading = true;

    try {
      const result = await bindEmployee({
        lineUserId: lineProfile?.userId,
        lineDisplayName: lineProfile?.displayName,
        linePictureUrl: lineProfile?.pictureUrl,
        employeeName: employeeName.trim()
      });

      if (result.success) {
        if (result.data.matched) {
          toastStore.success('綁定成功！歡迎 ' + result.data.name);
          onBindSuccess(result.data);
        } else {
          errorMessage = '找不到符合的員工資料，請確認姓名是否正確';
        }
      } else {
        errorMessage = result.error?.message || '綁定失敗，請稍後再試';
      }
    } catch (error) {
      console.error('Binding error:', error);
      errorMessage = '系統錯誤，請稍後再試';
    } finally {
      isLoading = false;
    }
  }

  function handleKeydown(event) {
    if (event.key === 'Enter') {
      handleSubmit();
    }
  }
</script>

<div class="min-h-screen bg-gray-100 flex flex-col">
  <!-- Header -->
  <div class="bg-line-green text-white px-4 py-4">
    <h1 class="text-lg font-bold text-center">員工綁定</h1>
  </div>

  <!-- Content -->
  <div class="flex-1 flex flex-col items-center justify-center p-6">
    <!-- LINE Profile Card -->
    <div class="bg-white rounded-2xl shadow-lg p-6 w-full max-w-sm mb-6">
      <div class="flex flex-col items-center">
        {#if lineProfile?.pictureUrl}
          <img
            src={lineProfile.pictureUrl}
            alt="LINE 頭像"
            class="w-20 h-20 rounded-full border-4 border-line-green mb-4"
          />
        {:else}
          <div class="w-20 h-20 rounded-full bg-gray-200 flex items-center justify-center mb-4">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
          </div>
        {/if}
        <p class="text-gray-500 text-sm">LINE 帳號</p>
        <p class="font-bold text-lg">{lineProfile?.displayName || '未知用戶'}</p>
      </div>
    </div>

    <!-- Binding Form -->
    <div class="bg-white rounded-2xl shadow-lg p-6 w-full max-w-sm">
      <div class="text-center mb-6">
        <div class="inline-flex items-center justify-center w-12 h-12 bg-green-50 rounded-full mb-3">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-line-green" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
          </svg>
        </div>
        <h2 class="text-lg font-bold text-gray-800">綁定您的員工帳號</h2>
        <p class="text-sm text-gray-500 mt-1">請輸入您在公司登記的中文姓名</p>
      </div>

      <div class="space-y-4">
        <div>
          <label for="employeeName" class="block text-sm font-medium text-gray-700 mb-2">
            員工中文姓名
          </label>
          <input
            id="employeeName"
            type="text"
            bind:value={employeeName}
            onkeydown={handleKeydown}
            placeholder="請輸入您的姓名"
            class="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-line-green focus:outline-none transition-colors
                   {errorMessage ? 'border-red-300' : ''}"
            disabled={isLoading}
          />
          {#if errorMessage}
            <p class="mt-2 text-sm text-red-500">{errorMessage}</p>
          {/if}
        </div>

        <button
          onclick={handleSubmit}
          disabled={isLoading || !employeeName.trim()}
          class="w-full py-3 px-4 rounded-xl font-bold text-white transition-all
                 {isLoading || !employeeName.trim()
                   ? 'bg-gray-300 cursor-not-allowed'
                   : 'bg-line-green hover:opacity-90 active:scale-[0.98]'}"
        >
          {#if isLoading}
            <span class="inline-flex items-center gap-2">
              <span class="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
              綁定中...
            </span>
          {:else}
            確認綁定
          {/if}
        </button>
      </div>

      <div class="mt-6 pt-4 border-t border-gray-100">
        <p class="text-xs text-gray-400 text-center">
          綁定後即可使用打卡功能<br/>
          如有問題請聯繫人資部門
        </p>
      </div>
    </div>
  </div>
</div>

<style>
  .bg-line-green {
    background-color: #06C755;
  }
  .border-line-green {
    border-color: #06C755;
  }
  .text-line-green {
    color: #06C755;
  }
</style>
