// LINE LIFF SDK 服務
import liff from '@line/liff';

const LIFF_ID = import.meta.env.VITE_LIFF_ID || '';
const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true';

class LiffService {
  constructor() {
    this.isInitialized = false;
    this.profile = null;
    this.error = null;
  }

  /**
   * 初始化 LIFF SDK
   * @returns {Promise<boolean>}
   */
  async init() {
    // Mock 模式
    if (USE_MOCK) {
      console.log('[LIFF] Mock mode enabled');
      this.isInitialized = true;
      this.profile = {
        userId: 'mock_user_001',
        displayName: '測試用戶',
        pictureUrl: 'https://via.placeholder.com/150'
      };
      return true;
    }

    if (!LIFF_ID) {
      console.error('[LIFF] LIFF_ID is not set');
      this.error = 'LIFF ID 未設定';
      return false;
    }

    try {
      await liff.init({ liffId: LIFF_ID });
      this.isInitialized = true;
      console.log('[LIFF] Initialized successfully');

      // 如果已登入，取得 profile
      if (liff.isLoggedIn()) {
        await this.loadProfile();
      }

      return true;
    } catch (error) {
      console.error('[LIFF] Init error:', error);
      this.error = error.message;
      return false;
    }
  }

  /**
   * 載入用戶 Profile
   */
  async loadProfile() {
    if (USE_MOCK) return;

    try {
      this.profile = await liff.getProfile();
      console.log('[LIFF] Profile loaded:', this.profile.displayName);
    } catch (error) {
      console.error('[LIFF] Get profile error:', error);
      this.error = error.message;
    }
  }

  /**
   * 檢查是否已登入
   * @returns {boolean}
   */
  isLoggedIn() {
    if (USE_MOCK) return true;
    return liff.isLoggedIn();
  }

  /**
   * 登入
   */
  login() {
    if (USE_MOCK) return;
    liff.login();
  }

  /**
   * 登出
   */
  logout() {
    if (USE_MOCK) return;
    liff.logout();
    this.profile = null;
  }

  /**
   * 取得用戶 Profile
   * @returns {Object|null}
   */
  getProfile() {
    return this.profile;
  }

  /**
   * 檢查是否在 LINE App 內
   * @returns {boolean}
   */
  isInClient() {
    if (USE_MOCK) return false;
    return liff.isInClient();
  }

  /**
   * 關閉 LIFF 視窗
   */
  closeWindow() {
    if (USE_MOCK) return;
    liff.closeWindow();
  }

  /**
   * 發送打卡成功訊息到 LINE
   * @param {string} type - 'in' 或 'out'
   * @param {string} time - 打卡時間
   */
  async sendClockMessage(type, time) {
    if (USE_MOCK || !liff.isInClient()) {
      console.log('[LIFF] Mock sendClockMessage:', type, time);
      return;
    }

    const typeText = type === 'in' ? '上班' : '下班';
    const now = new Date();
    const dateStr = `${now.getFullYear()}/${now.getMonth() + 1}/${now.getDate()}`;

    try {
      await liff.sendMessages([
        {
          type: 'flex',
          altText: `${typeText}打卡成功 ${time}`,
          contents: {
            type: 'bubble',
            size: 'kilo',
            header: {
              type: 'box',
              layout: 'vertical',
              contents: [
                {
                  type: 'text',
                  text: `${typeText}打卡成功`,
                  color: '#ffffff',
                  size: 'lg',
                  weight: 'bold'
                }
              ],
              backgroundColor: type === 'in' ? '#06C755' : '#5B82DB'
            },
            body: {
              type: 'box',
              layout: 'vertical',
              contents: [
                {
                  type: 'text',
                  text: dateStr,
                  size: 'sm',
                  color: '#aaaaaa'
                },
                {
                  type: 'text',
                  text: time,
                  size: 'xxl',
                  weight: 'bold',
                  margin: 'md'
                }
              ]
            }
          }
        }
      ]);
      console.log('[LIFF] Clock message sent');
    } catch (error) {
      console.error('[LIFF] Send message error:', error);
    }
  }

  /**
   * 取得錯誤訊息
   * @returns {string|null}
   */
  getError() {
    return this.error;
  }
}

export const liffService = new LiffService();
export default liffService;
