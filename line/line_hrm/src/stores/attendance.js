// 出勤狀態管理
import { writable, derived } from 'svelte/store';

function createAttendanceStore() {
  const { subscribe, set, update } = writable({
    status: 'not_clocked_in',  // not_clocked_in | clocked_in | clocked_out
    checkIn: null,
    checkInTime: null,
    checkOut: null,
    checkOutTime: null,
    lastClockResult: null,
  });

  return {
    subscribe,

    /**
     * 設定今日出勤狀態
     * @param {Object} data
     */
    setTodayAttendance(data) {
      set({
        status: data.status || 'not_clocked_in',
        checkIn: data.check_in || null,
        checkInTime: data.check_in_time || null,
        checkOut: data.check_out || null,
        checkOutTime: data.check_out_time || null,
        lastClockResult: null,
      });
    },

    /**
     * 上班打卡成功
     * @param {Object} result
     */
    setClockIn(result) {
      update(state => ({
        ...state,
        status: 'clocked_in',
        checkIn: result.datetime,
        checkInTime: result.time,
        lastClockResult: {
          type: 'in',
          time: result.time,
        },
      }));
    },

    /**
     * 下班打卡成功
     * @param {Object} result
     */
    setClockOut(result) {
      update(state => ({
        ...state,
        status: 'clocked_out',
        checkOut: result.datetime,
        checkOutTime: result.time,
        lastClockResult: {
          type: 'out',
          time: result.time,
        },
      }));
    },

    /**
     * 清除最後打卡結果
     */
    clearLastResult() {
      update(state => ({
        ...state,
        lastClockResult: null,
      }));
    },

    /**
     * 重置狀態
     */
    reset() {
      set({
        status: 'not_clocked_in',
        checkIn: null,
        checkInTime: null,
        checkOut: null,
        checkOutTime: null,
        lastClockResult: null,
      });
    }
  };
}

export const attendanceStore = createAttendanceStore();

// 衍生 store: 是否可以打上班卡
export const canClockIn = derived(
  attendanceStore,
  $att => $att.status === 'not_clocked_in'
);

// 衍生 store: 是否可以打下班卡
export const canClockOut = derived(
  attendanceStore,
  $att => $att.status === 'clocked_in'
);

// 衍生 store: 今日已完成打卡
export const isCompleted = derived(
  attendanceStore,
  $att => $att.status === 'clocked_out'
);
