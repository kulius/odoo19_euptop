// Toast 通知狀態管理
import { writable } from 'svelte/store';

function createToastStore() {
  const { subscribe, set, update } = writable({
    show: false,
    type: 'info',    // success | error | warning | info
    message: '',
    duration: 3000,
  });

  let timer = null;

  function showToast(type, message, duration = 3000) {
    if (timer) {
      clearTimeout(timer);
    }

    set({
      show: true,
      type,
      message,
      duration,
    });

    timer = setTimeout(() => {
      set({
        show: false,
        type: 'info',
        message: '',
        duration: 3000,
      });
    }, duration);
  }

  return {
    subscribe,

    /**
     * 顯示成功訊息
     * @param {string} message
     * @param {number} duration
     */
    success(message, duration = 3000) {
      showToast('success', message, duration);
    },

    /**
     * 顯示錯誤訊息
     * @param {string} message
     * @param {number} duration
     */
    error(message, duration = 4000) {
      showToast('error', message, duration);
    },

    /**
     * 顯示警告訊息
     * @param {string} message
     * @param {number} duration
     */
    warning(message, duration = 3500) {
      showToast('warning', message, duration);
    },

    /**
     * 顯示資訊訊息
     * @param {string} message
     * @param {number} duration
     */
    info(message, duration = 3000) {
      showToast('info', message, duration);
    },

    /**
     * 隱藏 Toast
     */
    hide() {
      if (timer) {
        clearTimeout(timer);
      }
      set({
        show: false,
        type: 'info',
        message: '',
        duration: 3000,
      });
    }
  };
}

export const toastStore = createToastStore();
