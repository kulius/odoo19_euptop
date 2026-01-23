# -*- coding: utf-8 -*-
import base64
import csv
import io
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
import pandas as pd
import pytz


class SlAttendanceImport(models.Model):
    _name = 'sl.attendance.import'
    _description = '打卡資料匯入'
    _rec_name = 'csv_filename'

    csv_file = fields.Binary(string='檔案', required=True, help='支援 CSV、Excel (xlsx/xls) 格式')
    csv_filename = fields.Char(string='檔案名稱')
    start_date = fields.Date(string='起始日期', required=True, default=fields.Date.today)
    end_date = fields.Date(string='結束日期', required=True, default=fields.Date.today)
    import_datetime = fields.Datetime(string='匯入時間', readonly=True, help='按下匯入按鈕的時間點')
    imported_count = fields.Integer(string='成功匯入筆數', readonly=True, default=0)
    skipped_count = fields.Integer(string='略過筆數', readonly=True, default=0)
    filtered_count = fields.Integer(string='過濾筆數', readonly=True, default=0)
    error_count = fields.Integer(string='錯誤筆數', readonly=True, default=0)
    result_message = fields.Text(string='匯入結果', readonly=True)

    def action_import_attendance(self):
        """匯入打卡資料"""
        self.ensure_one()
        
        # 記錄匯入時間點
        import_time = fields.Datetime.now()
        self.write({'import_datetime': import_time})
        
        if not self.csv_file:
            raise UserError(_('請先上傳檔案！'))
        
        if self.start_date > self.end_date:
            raise UserError(_('起始日期不能大於結束日期！'))
        
        try:
            file_data = base64.b64decode(self.csv_file)
            filename = self.csv_filename or ''
            filename_lower = filename.lower()
            
            if filename_lower.endswith('.csv'):
                df = pd.read_csv(io.BytesIO(file_data), encoding='utf-8-sig')
                file_type = 'CSV'
            elif filename_lower.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(io.BytesIO(file_data))
                file_type = 'Excel'
            else:
                raise UserError(_('不支援的檔案格式！請上傳 CSV 或 Excel (xlsx/xls) 檔案'))
            
            # ========== 判斷並標準化欄位格式 ==========
            # 格式 1: check_time + serial_number
            # 格式 2: Time + pin
            
            has_format1 = 'check_time' in df.columns and 'serial_number' in df.columns
            has_format2 = 'Time' in df.columns and 'pin' in df.columns
            
            if not has_format1 and not has_format2:
                raise UserError(_(
                    '檔案格式錯誤！請使用以下任一格式：\n'
                    '格式1: serial_number（工號）+ check_time（打卡時間）\n'
                    '格式2: time（打卡時間） + pin（PIN碼）'
                ))
            
            # 標準化欄位名稱
            if has_format2:
                # 格式 2: 將 Time 和 pin 轉換為標準欄位
                df = df.rename(columns={'Time': 'check_time', 'pin': 'serial_number'})
                
                # 處理 pin：補 S0 前綴（例如：12 -> S0012, 115 -> S0115）
                df['serial_number'] = df['serial_number'].apply(lambda x: 'S' + str(x).rjust(4, '0'))
            
            
            # ========== 使用 pandas 進行資料清理和過濾 ==========
            
            # 1. 移除空值行
            df = df.dropna(subset=['serial_number', 'check_time'])
            
            # 2. 清理工號
            df['serial_number'] = df['serial_number'].astype(str).str.strip()
            df = df[df['serial_number'] != '']
            
            # 3. 轉換打卡時間為 datetime
            if df['check_time'].dtype == 'object':
                # 字串格式，需要解析
                df['check_time'] = pd.to_datetime(df['check_time'], errors='coerce')
            elif pd.api.types.is_datetime64_any_dtype(df['check_time']):
                # 已經是 datetime 格式（Excel 自動轉換）
                pass
            else:
                # 其他格式嘗試轉換
                df['check_time'] = pd.to_datetime(df['check_time'], errors='coerce')
            
            # 移除無法解析的時間
            df = df.dropna(subset=['check_time'])
            
            # 4. 計算實際的時間範圍（考慮 6:00 AM 分界點）
            # 例如：選擇 2025-10-01 ~ 2025-10-03
            # 實際範圍：2025-10-01 06:00:00 ~ 2025-10-04 05:59:59
            from datetime import timedelta
            start_datetime = pd.Timestamp(datetime.combine(self.start_date, datetime.min.time()) + timedelta(hours=6))
            end_datetime = pd.Timestamp(datetime.combine(self.end_date + timedelta(days=1), datetime.min.time()) + timedelta(hours=6, seconds=-1))
            
            # 記錄過濾前的數量
            before_filter_count = len(df)
            
            # 過濾日期範圍（使用調整後的時間範圍）
            df = df[(df['check_time'] >= start_datetime) & (df['check_time'] <= end_datetime)]
            
            # 計算過濾掉的筆數
            filtered_count = before_filter_count - len(df)
            
            # 5. 按時間排序
            df = df.sort_values('check_time')
            
            # 6. 重置索引
            df = df.reset_index(drop=True)
            
            if len(df) == 0:
                raise UserError(_('沒有符合日期範圍的打卡記錄！'))
            
            # ========== 建立員工查找快取 ==========
            employee_tmp_memory = {}
            error_lines = []
            
            # 先查找所有唯一的工號對應的員工
            unique_serial_numbers = df['serial_number'].unique()
            for serial_number in unique_serial_numbers:
                employee = self._find_employee(serial_number, employee_tmp_memory)
                if not employee:
                    error_lines.append(f"找不到工號：{serial_number}")
            
            # 移除找不到員工的記錄
            df['employee_id'] = df['serial_number'].map(
                lambda x: employee_tmp_memory.get(str(x).strip(), None).id 
                if employee_tmp_memory.get(str(x).strip(), None) else None
            )
            df = df.dropna(subset=['employee_id'])
            df['employee_id'] = df['employee_id'].astype(int)
            
            # 取得本地時區（台灣時區 UTC+8）
            local_tz = pytz.timezone('Asia/Taipei')
            
            # ========== 在寫入前先移除重複的打卡記錄 ==========
            # 統一轉換時間格式並計算 UTC 時間（用於去重）
            df['check_time_utc'] = df['check_time'].apply(lambda x: 
                local_tz.localize(x.to_pydatetime()).astimezone(pytz.UTC).replace(tzinfo=None) 
                if x.to_pydatetime().tzinfo is None 
                else x.to_pydatetime().astimezone(pytz.UTC).replace(tzinfo=None)
            )
            
            # 記錄去重前的數量
            before_dedup_count = len(df)
            
            # 去除同一員工、同一時間點的重複記錄（保留第一筆）
            df = df.drop_duplicates(subset=['employee_id', 'check_time_utc'], keep='first')
            
            # 計算去重掉的筆數
            dedup_count = before_dedup_count - len(df)
            
            # ========== 轉換日期範圍為 UTC（用於資料庫查詢和刪除）==========
            # start_datetime 和 end_datetime 已經是調整後的時間（考慮 6:00 AM 分界點）
            start_datetime_local = local_tz.localize(start_datetime.to_pydatetime())
            end_datetime_local = local_tz.localize(end_datetime.to_pydatetime())
            start_datetime_utc = start_datetime_local.astimezone(pytz.UTC).replace(tzinfo=None)
            end_datetime_utc = end_datetime_local.astimezone(pytz.UTC).replace(tzinfo=None)
            
            # 初始化統計變數（在 transaction 外部也能訪問）
            deleted_raw_count = 0
            deleted_attendance_count = 0
            raw_created_count = 0
            raw_skipped_count = 0
            imported_count = 0
            raw_error_details = []
            attendance_error_details = []
            debug_info = []
            
            # ========== 使用 Transaction 確保資料一致性 ==========
            with self.env.cr.savepoint():
                # ========== 第一步：刪除區間內的舊資料（基於 UTC 時間範圍）==========
                # 刪除舊的 raw 記錄（來源為 manual 的記錄）
                old_raw_records = self.env['hr.attendance.raw'].search([
                    ('check_time', '>=', start_datetime_utc),
                    ('check_time', '<=', end_datetime_utc),
                    ('source', '=', 'manual'),  # 只刪除手動匯入的記錄
                ])
                deleted_raw_count = len(old_raw_records)
                old_raw_records.unlink()
                
                # 刪除舊的考勤記錄（check_in 在時間範圍內）
                old_attendances = self.env['hr.attendance'].search([
                    ('check_in', '>=', start_datetime_utc),
                    ('check_in', '<=', end_datetime_utc),
                ])
                deleted_attendance_count = len(old_attendances)
                old_attendances.unlink()
                
                # ========== 第二步：批量新增原始打卡記錄，並記錄成功寫入的資料 ==========
                successfully_created_records = []  # 記錄成功寫入的資料
                
                records = df.to_dict('records')
                for row in records:
                    # 將 pandas datetime 轉換為 Python datetime
                    dt = row['check_time'].to_pydatetime()
                    dt_utc = row['check_time_utc']  # 使用已經計算好的 UTC 時間
                    
                    # 如果沒有時區資訊，假設為本地時間
                    if dt.tzinfo is None:
                        dt = local_tz.localize(dt)
                    
                    # 建立 raw 記錄（因為已經去重，不應該有重複錯誤）
                    self.env['hr.attendance.raw'].create({
                        'employee_id': int(row['employee_id']),
                        'check_time': dt_utc,
                        'source': 'manual',
                    })
                    raw_created_count += 1
                    
                    # 記錄成功寫入的資料（保留本地時間用於後續處理）
                    successfully_created_records.append({
                        'employee_id': int(row['employee_id']),
                        'check_time': dt,  # 本地時間（帶時區）
                        'check_time_utc': dt_utc,  # UTC 時間
                    })
                
                # ========== 第三步：使用成功寫入的資料建立考勤記錄 ==========
                if len(successfully_created_records) == 0:
                    raise UserError(_('沒有成功寫入的打卡記錄！'))
                
                # 轉換為 DataFrame 方便處理
                df_created = pd.DataFrame(successfully_created_records)
                
                # 計算工作日期（使用本地時間）
                def get_work_date(dt):
                    """根據本地時間計算工作日期（6:00 AM 分界點）"""
                    if pd.isna(dt):
                        return None
                    # 轉換為本地時間（如果有時區）
                    if hasattr(dt, 'tzinfo') and dt.tzinfo is not None:
                        dt_local = dt.astimezone(local_tz) if hasattr(dt, 'astimezone') else dt
                    else:
                        dt_local = dt
                    
                    # 6:00 AM 分界點判斷
                    if dt_local.hour < 6:
                        return (dt_local - timedelta(days=1)).date()
                    else:
                        return dt_local.date()
                
                df_created['work_date'] = df_created['check_time'].apply(get_work_date)
                
                # 建立考勤記錄
                # 先按時間排序整個 DataFrame，確保順序正確
                df_created = df_created.sort_values(['employee_id', 'work_date', 'check_time']).reset_index(drop=True)
                
                # 按員工和工作日期分組
                grouped = df_created.groupby(['employee_id', 'work_date'], sort=False)
                
                for (employee_id, work_date), group in grouped:
                    try:
                        # 轉換 numpy.int64 為 Python int，避免 Odoo ORM 錯誤
                        employee_id = int(employee_id)
                        
                        # 確保按時間排序
                        records = group.sort_values('check_time').reset_index(drop=True)
                        
                        if len(records) == 0:
                            continue
                        
                        # 調試資訊：記錄該工作日的所有打卡時間
                        check_times = []
                        for idx, row in records.iterrows():
                            dt = row['check_time']
                            if hasattr(dt, 'strftime'):
                                check_times.append(dt.strftime('%Y-%m-%d %H:%M:%S'))
                            else:
                                check_times.append(str(dt))
                        
                        debug_info.append(f"員工 {employee_id} - 工作日 {work_date}: {len(records)} 筆打卡 -> {check_times[0]} ~ {check_times[-1]}")
                        
                        # 當日第一筆當作上班打卡（使用 UTC 時間）
                        first_check_time_utc = records.iloc[0]['check_time_utc']
                        
                        # 建立考勤記錄（包含 check_in 和 check_out）
                        attendance_data = {
                            'employee_id': employee_id,
                            'check_in': first_check_time_utc,
                        }
                        
                        # 如果有多筆記錄，最後一筆當作下班打卡（使用 UTC 時間）
                        if len(records) > 1:
                            last_check_time_utc = records.iloc[-1]['check_time_utc']
                            attendance_data['check_out'] = last_check_time_utc
                        else : # 有可能是忘記打上/下班卡，但都寫紀錄，讓異常單比較好對應
                            attendance_data['check_out'] = first_check_time_utc
                        
                        # 直接建立考勤記錄（不檢查重複，因為已刪除舊資料）
                        self.env['hr.attendance'].create(attendance_data)
                        imported_count += 1
                        
                    except Exception as e:
                        # 記錄考勤建立錯誤
                        error_msg = str(e)
                        if len(attendance_error_details) < 10:
                            attendance_error_details.append(f"員工 {employee_id} - 工作日 {work_date}: {error_msg[:200]}")
                        continue
            
            # Transaction 成功提交後
            skipped_count = 0  # 不再有略過的記錄（已刪除舊資料）
            
            result_message = self._format_result_message(
                file_type, imported_count, skipped_count, filtered_count, error_lines,
                deleted_raw_count, deleted_attendance_count, raw_created_count, raw_skipped_count,
                debug_info, raw_error_details, attendance_error_details, dedup_count
            )
            
            self.write({
                'imported_count': imported_count,
                'skipped_count': skipped_count,
                'filtered_count': filtered_count,
                'error_count': len(error_lines),
                'result_message': result_message,
            })
            
            # 建立詳細的通知訊息
            notification_message = f"📊 匯入統計\n\n"
            notification_message += f"📝 原始考勤記錄：\n"
            if dedup_count > 0:
                notification_message += f"  • 去除重複：{dedup_count} 筆\n"
            notification_message += f"  • 成功寫入：{raw_created_count} 筆\n"
            
            notification_message += f"\n✅ 考勤記錄：\n"
            notification_message += f"  • 成功匯入：{imported_count} 筆\n"
            if attendance_error_details and len(attendance_error_details) > 0:
                notification_message += f"  • 建立錯誤：{len(attendance_error_details)} 筆\n"
            
            if filtered_count > 0:
                notification_message += f"\n📊 過濾範圍外：{filtered_count} 筆"
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('✅ 匯入完成'),
                    'message': notification_message,
                    'type': 'success',
                    'sticky': True,  # 改為 sticky，讓使用者有時間閱讀統計資訊
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
            
        except Exception as e:
            raise UserError(_('匯入失敗：%s') % str(e))
    
    def _find_employee(self, serial_number, employee_tmp_memory):
        """查找員工（依序使用工號、條碼、PIN），並使用快取避免重複查詢"""
        key = str(serial_number)
        if key in employee_tmp_memory:
            return employee_tmp_memory[key]

        employee = self.env['hr.employee'].search([
            ('employee_number', '=', serial_number)
        ], limit=1)

        if not employee:
            employee = self.env['hr.employee'].search([
                ('barcode', '=', serial_number)
            ], limit=1)

        if not employee:
            employee = self.env['hr.employee'].search([
                ('pin', '=', serial_number)
            ], limit=1)

        employee_tmp_memory[key] = employee
        return employee
    
    def _format_pin(self, pin_value):
        """
        格式化 PIN 碼：補 S0 前綴
        例如：12 -> S0012, 115 -> S0115, 1 -> S0001
        """
        try:
            # 移除空白並轉為字串
            pin_str = str(pin_value).strip()
            
            # 如果已經有 S 前綴，直接返回
            if pin_str.startswith('S'):
                return pin_str
            
            # 嘗試轉換為整數（去除可能的小數點）
            try:
                pin_int = int(float(pin_str))
                pin_str = str(pin_int)
            except ValueError:
                # 如果無法轉換為數字，直接返回原值
                return pin_str
            
            # 補齊為 4 位數字，前面加 S0
            return f"S{pin_str.zfill(4)}"
        except Exception:
            return str(pin_value)
    
    def _format_result_message(self, file_type, imported_count, skipped_count, filtered_count, error_lines, 
                                deleted_raw_count=0, deleted_attendance_count=0, 
                                raw_created_count=0, raw_skipped_count=0, debug_info=None,
                                raw_error_details=None, attendance_error_details=None, dedup_count=0):
        """格式化結果訊息"""
        message = f"檔案類型：{file_type}\n"
        message += f"日期範圍：{self.start_date.strftime('%Y-%m-%d')} ~ {self.end_date.strftime('%Y-%m-%d')}\n\n"
        
        if deleted_raw_count > 0 or deleted_attendance_count > 0:
            message += f"🗑️ 清除舊資料：\n"
            message += f"  - 原始打卡記錄：{deleted_raw_count} 筆\n"
            message += f"  - 考勤記錄：{deleted_attendance_count} 筆\n\n"
        
        message += f"📝 原始打卡記錄：\n"
        if dedup_count > 0:
            message += f"  - 去除重複：{dedup_count} 筆（同一員工、同一時間）\n"
        message += f"  - 新增成功：{raw_created_count} 筆\n"
        if raw_skipped_count > 0:
            message += f"  - 略過重複：{raw_skipped_count} 筆\n"
        
        # 顯示 raw 記錄錯誤
        if raw_error_details and len(raw_error_details) > 0:
            message += f"  - Raw 記錄錯誤（前5筆）：\n"
            for err in raw_error_details:
                message += f"    {err}\n"
        
        message += f"\n✅ 考勤記錄：成功匯入 {imported_count} 筆\n"
        
        # 顯示考勤記錄錯誤
        if attendance_error_details and len(attendance_error_details) > 0:
            message += f"⚠️  考勤記錄錯誤（{len(attendance_error_details)} 筆）：\n"
            for err in attendance_error_details:
                message += f"  {err}\n"
        
        message += f"\n📊 過濾範圍外：{filtered_count} 筆\n"
        
        # 顯示調試資訊（前10筆）
        if debug_info and len(debug_info) > 0:
            message += f"\n🔍 考勤分組明細（前10筆）：\n"
            for info in debug_info[:10]:
                message += f"  {info}\n"
            if len(debug_info) > 10:
                message += f"  ... 還有 {len(debug_info) - 10} 筆\n"
        
        if error_lines:
            message += f"\n❌ 錯誤：{len(error_lines)} 筆\n"
            message += "錯誤明細：\n" + "\n".join(error_lines[:30])
            if len(error_lines) > 30:
                message += f"\n... 還有 {len(error_lines) - 30} 個錯誤未顯示"
        
        return message
    
    def _parse_datetime(self, datetime_str):
        """解析日期時間字串，支援多種格式"""
        if not datetime_str:
            return False
        
        # 支援的時間格式
        time_formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y/%m/%d %H:%M:%S',
            '%Y-%m-%d %H:%M',
            '%Y/%m/%d %H:%M',
            '%Y%m%d %H:%M:%S',
            '%Y%m%d %H:%M',
        ]
        
        for fmt in time_formats:
            try:
                return datetime.strptime(datetime_str, fmt)
            except ValueError:
                continue
        
        raise ValidationError(_('無法解析時間格式：%s（支援格式：YYYY-MM-DD HH:MM:SS 或 YYYY/MM/DD HH:MM:SS）') % datetime_str)
