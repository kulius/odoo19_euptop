// GPS 位置狀態管理
import { writable, derived } from 'svelte/store';

function createLocationStore() {
  const { subscribe, set, update } = writable({
    isSupported: true,
    isLoading: false,
    current: null,
    error: null,
  });

  return {
    subscribe,

    /**
     * 設定是否支援定位
     * @param {boolean} supported
     */
    setSupported(supported) {
      update(state => ({
        ...state,
        isSupported: supported,
      }));
    },

    /**
     * 開始取得位置
     */
    startLoading() {
      update(state => ({
        ...state,
        isLoading: true,
        error: null,
      }));
    },

    /**
     * 設定當前位置
     * @param {Object} position
     */
    setPosition(position) {
      update(state => ({
        ...state,
        isLoading: false,
        current: position,
        error: null,
      }));
    },

    /**
     * 設定錯誤
     * @param {string} error
     */
    setError(error) {
      update(state => ({
        ...state,
        isLoading: false,
        error,
      }));
    },

    /**
     * 清除位置
     */
    clear() {
      update(state => ({
        ...state,
        current: null,
        error: null,
      }));
    },

    /**
     * 重置狀態
     */
    reset() {
      set({
        isSupported: true,
        isLoading: false,
        current: null,
        error: null,
      });
    }
  };
}

export const locationStore = createLocationStore();

// 衍生 store: 是否有位置資料
export const hasLocation = derived(
  locationStore,
  $loc => $loc.current !== null
);

// 衍生 store: 格式化座標字串
export const formattedCoords = derived(
  locationStore,
  $loc => {
    if (!$loc.current) return '';
    const { latitude, longitude } = $loc.current;
    return `${latitude.toFixed(6)}, ${longitude.toFixed(6)}`;
  }
);
