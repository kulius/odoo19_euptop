from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import re


class WizardDependentsAdd(models.TransientModel):
    _name = 'wizard.dependents.add'

    relation = fields.Char(string='關係', required=True)
    name = fields.Char(string='姓名', required=True)
    health_rate = fields.Selection(string="政府補助健保費", selection=[('1', '無補助'), ('0.75', '補助1/4'), ('0.5', '補助1/2'), ('0', '免繳')], )
    identification_card = fields.Char(string='身分證')
    date_of_birth = fields.Date(string='生日')
    add_insurance_time = fields.Date(string='加保時間')
    cancel_insurance_time = fields.Date(string='退保時間')
    note = fields.Char(string='備註')

    # 使用Regular Expression 檢查身分證格式
    @api.constrains('identification_card')
    def verifyID(self):
        for i in self:
            if i.identification_card:
                if not re.match(r'^[A-Z][1-2]\d{8}$', i.identification_card):
                    raise ValidationError(_('眷保明細中的%s身分證格式錯誤' % i.name))
                else:
                    identification_card = i.identification_card.upper()  # 確保身分證號碼轉換成大寫
                    region_mapping = {'A': '10', 'B': '11', 'C': '12', 'D': '13', 'E': '14', 'F': '15', 'G': '16', 'H': '17',
                                      'I': '34', 'J': '18', 'K': '19', 'L': '20', 'M': '21', 'N': '22', 'O': '35', 'P': '23',
                                      'Q': '24', 'R': '25', 'S': '26', 'T': '27', 'U': '28', 'V': '29', 'W': '32', 'X': '30',
                                      'Y': '31', 'Z': '33'}
                    check_digit_weights = [1, 9, 8, 7, 6, 5, 4, 3, 2, 1, 1]

                    region = region_mapping.get(identification_card[0])
                    gender = identification_card[1]
                    serial_number = identification_card[2:9]

                    check_sum = int(region[0]) * int(check_digit_weights[0])
                    check_sum += int(region[1]) * int(check_digit_weights[1])
                    check_sum += int(gender) * int(check_digit_weights[2])

                    for j in range(3, 10):
                        check_num = int(serial_number[j - 3]) * int(check_digit_weights[j])
                        print(check_num)
                        check_sum += check_num

                    check_digit = (10 - (check_sum % 10)) % 10

                    if int(check_digit) == int(identification_card[9]):
                        return "檢查碼正確"
                    else:
                        raise ValidationError(_('眷保明細中的%s身分證格式錯誤' % i.name))

    def add(self):
        self.ensure_one()
        user_id = self.env.context.get('active_id')

        # 新增一筆眷保明細
        self.env['hr.dependents.information'].create({
            'employee_id': user_id,
            'name': self.name,
            'relation': self.relation,
            'identification_card': self.identification_card,
            'date_of_birth': self.date_of_birth,
            'add_insurance_time': self.add_insurance_time,
            'cancel_insurance_time': self.cancel_insurance_time,
            'note': self.note,
            'health_rate': self.health_rate
        })