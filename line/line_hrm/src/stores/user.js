// 用戶狀態管理
import { writable, derived } from 'svelte/store';

function createUserStore() {
  const { subscribe, set, update } = writable({
    isLoggedIn: false,
    profile: null,      // LINE Profile
    employee: null,     // Odoo 員工資料
  });

  return {
    subscribe,

    /**
     * 設定登入狀態
     * @param {Object} profile - LINE Profile
     * @param {Object} employee - Odoo 員工資料
     */
    setLoggedIn(profile, employee) {
      set({
        isLoggedIn: true,
        profile,
        employee,
      });
    },

    /**
     * 更新員工資料
     * @param {Object} employee
     */
    setEmployee(employee) {
      update(state => ({
        ...state,
        employee,
      }));
    },

    /**
     * 登出
     */
    logout() {
      set({
        isLoggedIn: false,
        profile: null,
        employee: null,
      });
    },

    /**
     * 重置狀態
     */
    reset() {
      set({
        isLoggedIn: false,
        profile: null,
        employee: null,
      });
    }
  };
}

export const userStore = createUserStore();

// 衍生 store: 員工姓名
export const employeeName = derived(
  userStore,
  $user => $user.employee?.name || ''
);

// 衍生 store: 部門名稱
export const departmentName = derived(
  userStore,
  $user => $user.employee?.department || ''
);
