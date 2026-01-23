// Odoo REST API 服務

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8069';
const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true';

// 快取 LINE User ID
let cachedLineUserId = null;

/**
 * 設定 LINE User ID (登入後呼叫)
 * @param {string} userId
 */
export function setLineUserId(userId) {
  cachedLineUserId = userId;
}

/**
 * 取得 LINE User ID
 * @returns {string|null}
 */
export function getLineUserId() {
  return cachedLineUserId;
}

/**
 * 統一 API 請求方法
 * @param {string} endpoint - API 端點
 * @param {Object} options - fetch 選項
 * @returns {Promise<Object>}
 */
async function apiRequest(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;

  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  // 自動加入 LINE User ID
  if (cachedLineUserId) {
    headers['X-Line-User-Id'] = cachedLineUserId;
  }

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    const data = await response.json();

    if (!response.ok) {
      return {
        success: false,
        error: data.error || {
          code: 'HTTP_ERROR',
          message: `HTTP ${response.status}: ${response.statusText}`
        }
      };
    }

    return data;
  } catch (error) {
    console.error('[API] Request error:', error);
    return {
      success: false,
      error: {
        code: 'NETWORK_ERROR',
        message: '網路連線失敗，請稍後再試'
      }
    };
  }
}

// ==================== Mock API ====================

const mockEmployee = {
  id: 1,
  employee_id: 1,
  name: '測試員工',
  department: '資訊部',
  department_id: 1,
  job_title: '工程師',
  line_user_id: 'mock_user_001',
  line_display_name: '測試用戶',
  picture_url: 'https://via.placeholder.com/150'
};

let mockAttendance = {
  status: 'not_clocked_in',
  check_in: null,
  check_out: null
};

const mockHistory = [
  { id: 1, date: '2026-01-22', weekday: '四', check_in: '09:00', check_out: '18:00', worked_hours: 9 },
  { id: 2, date: '2026-01-21', weekday: '三', check_in: '08:55', check_out: '18:10', worked_hours: 9.25 },
  { id: 3, date: '2026-01-20', weekday: '二', check_in: '09:05', check_out: '17:50', worked_hours: 8.75 },
];

/**
 * 檢查用戶是否已綁定
 * @param {Object} liffProfile - LINE LIFF 用戶資料
 * @returns {Promise<Object>}
 */
export async function checkBinding(liffProfile) {
  const { userId, displayName, pictureUrl } = liffProfile;
  setLineUserId(userId);

  if (USE_MOCK) {
    return {
      success: true,
      isBound: true,
      data: mockEmployee
    };
  }

  return apiRequest('/api/line/check-binding', {
    method: 'POST',
    body: JSON.stringify({
      userId,
      displayName,
      pictureUrl,
    }),
  });
}

/**
 * 員工綁定（用姓名綁定 LINE 帳號）
 * @param {Object} params - {lineUserId, lineDisplayName, linePictureUrl, employeeName}
 * @returns {Promise<Object>}
 */
export async function bindEmployee(params) {
  const { lineUserId, lineDisplayName, linePictureUrl, employeeName } = params;

  if (USE_MOCK) {
    if (employeeName === '測試員工') {
      return {
        success: true,
        data: { matched: true, ...mockEmployee }
      };
    }
    return {
      success: true,
      data: { matched: false }
    };
  }

  return apiRequest('/api/line/bind', {
    method: 'POST',
    body: JSON.stringify({
      line_user_id: lineUserId,
      line_display_name: lineDisplayName,
      line_picture_url: linePictureUrl,
      employee_name: employeeName,
    }),
  });
}

/**
 * 取得用戶資料
 * @returns {Promise<Object>}
 */
export async function getUser() {
  if (USE_MOCK) {
    return { success: true, data: mockEmployee };
  }

  return apiRequest('/api/line/user', {
    method: 'GET',
  });
}

/**
 * 取得今日打卡狀態
 * @returns {Promise<Object>}
 */
export async function getTodayAttendance() {
  if (USE_MOCK) {
    return { success: true, data: mockAttendance };
  }

  return apiRequest('/api/line/attendance/today', {
    method: 'GET',
  });
}

/**
 * 打卡 (上班/下班)
 * @param {Object} params - {type, latitude, longitude, accuracy}
 * @returns {Promise<Object>}
 */
export async function clock(params) {
  if (USE_MOCK) {
    const now = new Date();
    const time = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;
    const datetime = now.toISOString().replace('T', ' ').substring(0, 19);

    if (params.type === 'in') {
      mockAttendance = {
        status: 'clocked_in',
        check_in: datetime,
        check_in_time: time,
        check_out: null
      };
      return {
        success: true,
        data: {
          id: 100,
          type: 'in',
          status: 'clocked_in',
          time,
          datetime,
          latitude: params.latitude,
          longitude: params.longitude
        }
      };
    } else {
      mockAttendance = {
        ...mockAttendance,
        status: 'clocked_out',
        check_out: datetime,
        check_out_time: time
      };
      return {
        success: true,
        data: {
          id: 100,
          type: 'out',
          status: 'clocked_out',
          time,
          datetime,
          latitude: params.latitude,
          longitude: params.longitude
        }
      };
    }
  }

  return apiRequest('/api/line/attendance/clock', {
    method: 'POST',
    body: JSON.stringify(params),
  });
}

/**
 * 取得出勤歷史
 * @param {number} limit - 筆數限制
 * @param {number} offset - 偏移量
 * @returns {Promise<Object>}
 */
export async function getAttendanceHistory(limit = 30, offset = 0) {
  if (USE_MOCK) {
    return {
      success: true,
      data: {
        records: mockHistory,
        total: mockHistory.length
      }
    };
  }

  return apiRequest(`/api/line/attendance/history?limit=${limit}&offset=${offset}`, {
    method: 'GET',
  });
}
