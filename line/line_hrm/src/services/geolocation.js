// GPS 定位服務模組

class GeolocationService {
  constructor() {
    this.watchId = null;
    this.lastPosition = null;
    this.error = null;
  }

  /**
   * 檢查是否支援 Geolocation API
   * @returns {boolean}
   */
  isSupported() {
    return 'geolocation' in navigator;
  }

  /**
   * 取得當前位置
   * @param {Object} options - 定位選項
   * @returns {Promise<Object>} 位置資訊
   */
  async getCurrentPosition(options = {}) {
    if (!this.isSupported()) {
      throw new Error('您的瀏覽器不支援定位功能');
    }

    const defaultOptions = {
      enableHighAccuracy: true,
      timeout: 15000,
      maximumAge: 0
    };

    const mergedOptions = { ...defaultOptions, ...options };

    return new Promise((resolve, reject) => {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const result = {
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy: position.coords.accuracy,
            altitude: position.coords.altitude,
            altitudeAccuracy: position.coords.altitudeAccuracy,
            heading: position.coords.heading,
            speed: position.coords.speed,
            timestamp: position.timestamp
          };

          this.lastPosition = result;
          this.error = null;
          resolve(result);
        },
        (error) => {
          this.error = this.parseError(error);
          reject(this.error);
        },
        mergedOptions
      );
    });
  }

  /**
   * 開始監聽位置變化
   * @param {Function} onSuccess - 成功回調
   * @param {Function} onError - 錯誤回調
   * @param {Object} options - 定位選項
   * @returns {number} watchId
   */
  watchPosition(onSuccess, onError, options = {}) {
    if (!this.isSupported()) {
      onError(new Error('您的瀏覽器不支援定位功能'));
      return null;
    }

    const defaultOptions = {
      enableHighAccuracy: true,
      timeout: 15000,
      maximumAge: 0
    };

    const mergedOptions = { ...defaultOptions, ...options };

    this.watchId = navigator.geolocation.watchPosition(
      (position) => {
        const result = {
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          accuracy: position.coords.accuracy,
          timestamp: position.timestamp
        };

        this.lastPosition = result;
        this.error = null;
        onSuccess(result);
      },
      (error) => {
        this.error = this.parseError(error);
        onError(this.error);
      },
      mergedOptions
    );

    return this.watchId;
  }

  /**
   * 停止監聽位置
   */
  clearWatch() {
    if (this.watchId !== null) {
      navigator.geolocation.clearWatch(this.watchId);
      this.watchId = null;
    }
  }

  /**
   * 解析 Geolocation 錯誤
   * @param {GeolocationPositionError} error
   * @returns {Error}
   */
  parseError(error) {
    let message = '';
    let code = error.code;

    switch (error.code) {
      case error.PERMISSION_DENIED:
        message = '定位權限被拒絕，請允許使用位置資訊';
        break;
      case error.POSITION_UNAVAILABLE:
        message = '無法取得位置資訊，請確認 GPS 已開啟';
        break;
      case error.TIMEOUT:
        message = '定位超時，請稍後再試';
        break;
      default:
        message = '發生未知的定位錯誤';
    }

    const err = new Error(message);
    err.code = code;
    err.originalError = error;
    return err;
  }

  /**
   * 計算兩點之間的距離（公尺）
   * @param {number} lat1
   * @param {number} lon1
   * @param {number} lat2
   * @param {number} lon2
   * @returns {number} 距離（公尺）
   */
  calculateDistance(lat1, lon1, lat2, lon2) {
    const R = 6371000; // 地球半徑（公尺）
    const dLat = this.toRad(lat2 - lat1);
    const dLon = this.toRad(lon2 - lon1);
    const a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(this.toRad(lat1)) * Math.cos(this.toRad(lat2)) *
      Math.sin(dLon / 2) * Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
  }

  /**
   * 角度轉弧度
   * @param {number} deg - 角度
   * @returns {number} 弧度
   */
  toRad(deg) {
    return deg * (Math.PI / 180);
  }

  /**
   * 取得最後一次位置
   * @returns {Object|null}
   */
  getLastPosition() {
    return this.lastPosition;
  }

  /**
   * 取得最後一次錯誤
   * @returns {Error|null}
   */
  getLastError() {
    return this.error;
  }
}

// 匯出單例
export const geolocationService = new GeolocationService();
export default geolocationService;
