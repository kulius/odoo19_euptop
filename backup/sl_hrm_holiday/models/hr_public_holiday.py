from odoo import api, fields, models
import datetime
import pytz


class HrPublicHoliday(models.Model):
    _name = 'hr.public.holiday'
    _description = '國定假日/補班日設定'

    name = fields.Char(string='名稱')
    holiday_type = fields.Selection([('day_off', '休假日'), ('regular_holiday', '例假日'), ('holiday', '國定假日'),
                                     ('make_up_day', '補班日')], string='休假類型')
    start_date = fields.Datetime(string='開始時間')
    end_date = fields.Datetime(string='結束時間')
    date = fields.Date(string='日期', required=True)
    # 原本只有start、end 兩個時間設定，但是用datetime的方式來處哩，會導致其他地方的判斷難度大增，
    # 如果把公眾假日限制日為單位，比較好做事，
    # 如果遇到公司自己彈性放假等，那就用休假的方式處裡那段時間，所以有人資批次休假的功能
    @api.model
    def create(self, vals):
        # 自動將end_date設定為23:59:59
        time_vals = datetime.datetime.strptime(vals.get('date'), '%Y-%m-%d')
        vals['start_date'] = time_vals.strftime('%Y-%m-%d 00:00:00')
        time_vals = time_vals.replace(hour=23, minute=59, second=59)
        vals['end_date'] = time_vals.strftime('%Y-%m-%d %H:%M:%S')

        if vals['name'] == '補行上班':
            vals['holiday_type'] = 'make_up_day'
        elif vals['name'] == '例假日' and time_vals.weekday() == 5:
            vals['holiday_type'] = 'day_off'
        elif vals['name'] == '例假日' and time_vals.weekday() == 6:
            vals['holiday_type'] = 'regular_holiday'
        else:
            vals['holiday_type'] = 'holiday'
        return super(HrPublicHoliday, self).create(vals)

    def is_duraction_has_holiday(self, start_date, end_date):
        has_holiday = self.search([
            ('start_date', '<=', end_date),
            ('end_date', '>=', start_date),
            ('holiday_type', '!=', 'make_up_day')
        ])
        return has_holiday if has_holiday else False
    
    def datetime_convert(self, date):
        # 公眾假日的時間莫名其妙不是UTC+8，參照其他地方程式碼做這樣的轉換
        user_tz = self.env.user.tz or 'UTC'
        local_tz = pytz.timezone(user_tz)
        date = local_tz.localize(date).astimezone(pytz.utc)
        return date.strftime('%Y-%m-%d %H:%M:%S')