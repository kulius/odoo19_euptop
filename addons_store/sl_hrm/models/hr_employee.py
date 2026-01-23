import datetime
import re

from odoo import models, fields, api
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError, UserError


class HrEmployeeInheritance(models.Model):
    _inherit = "hr.employee"
    _order = "employee_number asc"

    employee_number = fields.Char(string="員工編號", groups="hr.group_hr_user")
    name_eng = fields.Char(string="英文姓名", groups="hr.group_hr_user")
    # company_site_id = fields.Many2one('sl.company.site', string='工務所')
    work_location_id = fields.Many2one("hr.work.location", "工務所")
    substitute_id = fields.Many2one(
        "hr.employee.public", string="代理人", groups="hr.group_hr_user"
    )
    certificate = fields.Selection(
        string="學歷",
        selection=[
            ("doctor", "博士"),
            ("master", "碩士"),
            ("bachelor", "大學"),
            ("graduate", "專科"),
            ("other", "高中職(含)以下"),
        ],
    )

    job_tenure = fields.Char(
        string="工作年資", compute="display_job_tenure_compute")
    job_tenure_count = fields.Float(
        string="工作年資", compute="job_tenure_compute")
    past_job_tenure_years = fields.Integer(string="過往年資(年)")
    past_job_tenure_months = fields.Integer(string="過往年資(月)")
    past_job_tenure_days = fields.Integer(string="過往年資(日)")

    # 私人資訊
    email = fields.Char(string="電子郵件", groups="hr.group_hr_user")
    telephone = fields.Char(string="電話", groups="hr.group_hr_user")
    cellphone = fields.Char(string="手機", groups="hr.group_hr_user")

    country_id = fields.Many2one(
        "res.country", default=lambda self: self.env.company.country_id)
    street = fields.Char(groups="hr.group_hr_user")
    street2 = fields.Char(groups="hr.group_hr_user")
    zip = fields.Char(change_default=True, groups="hr.group_hr_user")
    city = fields.Char(groups="hr.group_hr_user")
    state_id = fields.Many2one(
        "res.country.state",
        string="State",
        ondelete="restrict",
        domain="[('country_id', " "'=?', country_id)]",
        groups="hr.group_hr_user",
    )
    city_id = fields.Many2one(
        "res.city", string="City of Address", groups="hr.group_hr_user"
    )

    # 性別 (Odoo 19 移除了此欄位，需自行定義)
    gender = fields.Selection(
        selection=[
            ("male", "男"),
            ("female", "女"),
            ("other", "其他"),
        ],
        string="性別",
        groups="hr.group_hr_user",
    )

    # 血型
    blood_type = fields.Selection(
        selection=[
            ("A", "A型"),
            ("B", "B型"),
            ("AB", "AB型"),
            ("O", "O型"),
        ],
        string="血型",
    )

    employee_comment = fields.Text(string="備註")

    registration_date = fields.Date(string="入職日期", readonly=True, store=True)
    registration_remark = fields.Char(string="入職備註", default="入職")
    resignation_date = fields.Date(string="離職日期", readonly=True, store=True)
    resignation_reason = fields.Char(string="離職原因")
    hr_employee_working_ids = fields.One2many(
        "hr.employee.working", "employee_id", string="在離職異動歷程"
    )

    # MVPN
    mvpn = fields.Char(string="MVPN", groups="hr.group_hr_user")
    # 公司分機
    office_phone = fields.Char(string="公司分機", groups="hr.group_hr_user")

    # 產生戶籍相關欄位
    is_same_as_private_address = fields.Boolean(
        string="同通訊地址", groups="hr.group_hr_user"
    )
    register_country_id = fields.Many2one(
        "res.country", string="國家", groups="hr.group_hr_user"
    )
    register_city = fields.Char(string="都市", groups="hr.group_hr_user")
    register_state_id = fields.Many2one(
        "res.country.state",
        string="鄉鎮市區",
        ondelete="restrict",
        domain="[('country_id', " "'=?', register_country_id)]",
    )
    register_zip = fields.Char(string="郵遞區號")
    register_street = fields.Char(string="地址")
    register_street2 = fields.Char(string="地址")

    # 緊急聯絡人2
    emergency_contact2 = fields.Char(string="緊急聯絡人")
    # 緊急聯絡人關係2
    emergency_relation2 = fields.Char(string="關係")
    # 緊急聯絡人電話2
    emergency_phone2 = fields.Char(string="電話")

    emergency_contact_ids = fields.One2many(
        "starrylord.hr.emergency.contact", "employee_id", string="緊急聯絡人"
    )

    # 身分證正面影本
    id_card_front = fields.Binary(string="身分證正面影本")
    id_card_front_name = fields.Char(string="身分證正面影本名稱")

    # 身分證反面影本
    id_card_back = fields.Binary(string="身分證影本")
    id_card_back_name = fields.Char(string="身分證反面影本名稱")
    id_card_ids = fields.Many2many("ir.attachment", string="身分證影本")

    driving_license_ids = fields.Many2many(
        "ir.attachment",
        relation="m2m_ir_driving_license_rel",
        column1="m2m_id",
        column2="attachment_id",
        string="駕照",
    )
    insurance_doc_line_ids = fields.One2many(
        "sl.hr.insurance.doc", string="保險文件資料", inverse_name="employee_id"
    )
    health_report_line_ids = fields.One2many(
        "sl.health.report.line", string="體檢報告資料", inverse_name="employee_id"
    )
    license_line_ids = fields.One2many(
        "sl.hr.license.line", string="證照明細", inverse_name="employee_id"
    )

    # 健保
    # health_insurance_gap = fields.Float(string='健保投保級距', groups="hr.group_hr_user", default=False, readonly=True)
    health_insurance_family_number = fields.Selection(
        string="健保人數",
        selection=[
            ("0", "0"),
            ("1", "1"),
            ("2", "2"),
            ("3", "3"),
            ("4", "4"),
            ("5", "5"),
        ],
        groups="hr.group_hr_user",
        default="0",
    )
    # labor_insurance_gap = fields.Float(string='勞保投保級距', groups="hr.group_hr_user", default=False, readonly=True)

    labor_pension_gap_id = fields.Many2one(
        "hr.labor.pension.gap",
        string="勞退薪資級距",
        groups="hr.group_hr_user",
        default=False,
        compute="_compute_labor_pension_gap",
    )
    labor_harm_insurance_gap_id = fields.Many2one(
        "hr.labor.harm.insurance.gap",
        string="勞工職業災害保險級距",
        groups="hr.group_hr_user",
        default=False,
        compute="_compute_labor_harm_insurance_gap",
    )
    hr_health_insurance_gap_id = fields.Many2one(
        "hr.health.insurance.gap",
        string="健保投保級距",
        groups="hr.group_hr_user",
        default=False,
        compute="_compute_health_insurance_gap",
    )
    hr_labor_insurance_gap_id = fields.Many2one(
        "hr.labor.insurance.gap",
        string="勞保投保級距",
        groups="hr.group_hr_user",
        default=False,
        compute="_compute_labor_insurance_gap",
    )

    # sl_employee_payslip_ids = fields.One2many('hr.employee.payslip.setting', 'employee_id', string='薪資設定')

    labor_pension_history_ids = fields.One2many(
        "hr.labor.pension.history", "employee_id", string="勞退異動資料"
    )
    # 勞保異動歷程
    labor_insurance_history_ids = fields.One2many(
        "hr.labor.insurance.history",
        "labor_insurance_history_id",
        string="勞保異動資料",
    )
    # 健保異動歷程
    health_insurance_history_ids = fields.One2many(
        "hr.health.insurance.history",
        "health_insurance_history_id",
        string="健保異動資料",
    )
    labor_harm_insurance_history_ids = fields.One2many(
        "hr.labor.harm.insurance.history", "employee_id", string="勞工職業災害投保異動"
    )
    dependents_ids = fields.One2many(
        "hr.dependents.information", "employee_id", string="眷保明細"
    )

    bank_account_ids = fields.Many2many("res.partner.bank", string="銀行帳戶資訊")
    month_of_birthday = fields.Char(
        string="生日月份", compute="_compute_month_of_birthday", store=True
    )

    state = fields.Selection(
        selection=[("draft", "草稿"), ("working", "在職"), ("resign", "離職")],
        default="draft",
        compute="compute_state",
        string="狀態",
        store=True,
    )
    is_onboard = fields.Boolean(string="是否在職", compute="compute_state")

    dependents = fields.Selection(
        selection=[(str(i), str(i)) for i in range(12)],
        string="扶養人數",
        default="0",
        groups="hr.group_hr_user",
    )
    is_foreign = fields.Boolean(
        string="外籍員工", help="是否為外籍員工", groups="hr.group_hr_user", default=False,
    )

    is_no_need_check_in = fields.Boolean(
        string="無需打卡", help="是否為無需打卡的員工", groups="hr.group_hr_user", default=False,
    )

    # 從 sl_hrm_personal_calendar 合併
    schedule_id = fields.Many2one('hr.schedule', string='適用班別')

    _sql_constraints = [
        ("employee_number_uniq", "unique (employee_number)", "員工編號不能重複!"),
    ]

    @api.depends("birthday")
    def _compute_month_of_birthday(self):
        # 計算出生日的月份
        for rec in self:
            if rec.birthday:
                month_of_birthday = datetime.date.strftime(rec.birthday, "%m")
                rec.month_of_birthday = month_of_birthday

    @api.depends(
        "hr_employee_working_ids",
        "hr_employee_working_ids.start_date",
        "hr_employee_working_ids.change_reason_selection",
    )
    def compute_state(self):
        for rec in self:
            employee_working = rec.hr_employee_working_ids.filtered(
                lambda x: x.start_date <= datetime.datetime.now().date()
            ).sorted("start_date", reverse=True)[:1]
            rec.is_onboard = True
            # 計算入職日期
            employee_working_onboard = rec.hr_employee_working_ids.filtered(
                lambda x: x.change_reason_selection == "on_board"
            ).sorted("start_date", reverse=True)[:1]
            if employee_working_onboard:
                rec.registration_date = employee_working_onboard.start_date

            if employee_working.change_reason_selection in [
                "on_board",
                "reinstatement",
                "furlough",
            ]:
                rec.state = "working"
                rec.is_onboard = True

            elif employee_working.change_reason_selection == "resign":
                rec.state = "resign"
                rec.is_onboard = False
            else:
                rec.state = "draft"
                rec.is_onboard = False

            rec.resignation_date = False
            if rec.state == "resign":
                # 計算離職日期
                employee_working_resign = rec.hr_employee_working_ids.filtered(
                    lambda x: x.change_reason_selection == "resign"
                ).sorted("start_date", reverse=True)[:1]
                if employee_working_resign:
                    rec.resignation_date = employee_working_resign.start_date

    def registration_date_compute(self):  # 計算入職日期
        for rec in self:
            rec.registration_date = False
            if rec.state == "resign":
                employee_working = rec.hr_employee_working_ids.filtered(
                    lambda x: x.change_reason_selection == "on_board"
                ).sorted("start_date", reverse=True)[:1]
                if employee_working:
                    rec.registration_date = employee_working.start_date

    def resignation_date_compute(self):  # 計算離職日期
        for rec in self:
            rec.resignation_date = False
            employee_working = rec.hr_employee_working_ids.filtered(
                lambda x: x.change_reason_selection == "resign"
            ).sorted("start_date", reverse=True)[:1]
            if employee_working:
                rec.resignation_date = employee_working.start_date

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            company_id = vals.get("company_id")
            if not company_id:
                company_id = self.env.user.company_id.id

            res_company = self.env["res.company"].browse(company_id)

            # 年份（兩碼）
            search_year = fields.Date.today().strftime("%y")

            # 避免 employee_number_prefix 為 False（布林值）
            prefix = res_company.employee_number_prefix or ""

            search_prefix = prefix + search_year

            # 找出相同前綴的最大編號
            domain = [("employee_number", "ilike", search_prefix)]
            m_search = self.env["hr.employee"].search(domain)

            max_seq_no = (
                max(
                    m_search.mapped(
                        lambda x: int(
                            re.search(r"(\d{3})$", x.employee_number).group(1)
                        )
                    )
                )
                if m_search
                else 0
            )

            serial_number = search_prefix + str(max_seq_no + 1).zfill(3)
            vals["employee_number"] = serial_number

        records = super(HrEmployeeInheritance, self).create(vals_list)

        # 設定附件為 public
        for rec in records:
            for attachment in rec.id_card_ids:
                attachment.sudo().public = True
            for attachment in rec.driving_license_ids:
                attachment.sudo().public = True
            for line in rec.health_report_line_ids:
                line.health_report_upload.sudo().public = True
            for line in rec.license_line_ids:
                line.license_upload.sudo().public = True

        return records

    def write(self, vals):
        data = super(HrEmployeeInheritance, self).write(vals)
        for rec in self:
            for attachment in rec.id_card_ids:
                attachment.sudo().public = True
            for attachment in rec.driving_license_ids:
                attachment.sudo().public = True
            for line in rec.health_report_line_ids:
                line.health_report_upload.sudo().public = True
            for line in rec.license_line_ids:
                line.license_upload.sudo().public = True
        return data

    @api.onchange("is_same_as_private_address")
    def onchange_set_private_address(self):
        # 將戶籍地欄位設定成跟私人地址相同
        if self.is_same_as_private_address:
            self.register_country_id = self.private_country_id
            self.register_city = self.private_city
            self.register_zip = self.private_zip
            self.register_street = self.private_street
            self.register_street2 = self.private_street2
            self.register_state_id = self.private_state_id

    def job_tenure_return(self, date=datetime.date.today()):
        for rec in self:
            working_state = rec.hr_employee_working_ids.filtered(
                lambda r: r.start_date != False
            ).sorted("start_date", reverse=True)[:1]
            if (
                working_state.change_reason_selection != "resign"
                or working_state.change_reason_selection != "furlough"
            ):
                if working_state:
                    tenure = relativedelta(
                        (
                            date
                            + relativedelta(
                                years=+rec.past_job_tenure_years,
                                months=+rec.past_job_tenure_months,
                                days=+rec.past_job_tenure_days,
                            )
                        ),
                        working_state.start_date,
                    )
                    return float(tenure.years + tenure.months / 12)
                else:
                    return 0

    def display_job_tenure_compute(self):
        for rec in self:
            working_state = rec.hr_employee_working_ids.filtered(
                lambda r: r.start_date != False
            ).sorted("start_date", reverse=True)[:1]
            if (
                working_state.change_reason_selection == "resign"
                or working_state.change_reason_selection == "furlough"
            ):
                last_working = rec.hr_employee_working_ids.sorted(
                    "start_date", reverse=True
                )[:2]
                if len(last_working) == 2:
                    tenure = relativedelta(
                        (
                            last_working[0].start_date
                            + relativedelta(
                                years=+rec.past_job_tenure_years,
                                months=+rec.past_job_tenure_months,
                                days=+rec.past_job_tenure_days,
                            )
                        ),
                        last_working[1].start_date,
                    )
                try:
                    rec.job_tenure = (
                        str(tenure.years)
                        + "年"
                        + str(tenure.months)
                        + "個月"
                        + str(tenure.days)
                        + "天"
                    )
                except:
                    rec.job_tenure = "0年0個月0天"
            else:
                if working_state:
                    tenure = relativedelta(
                        (
                            datetime.date.today()
                            + relativedelta(
                                years=+rec.past_job_tenure_years,
                                months=+rec.past_job_tenure_months,
                                days=+rec.past_job_tenure_days,
                            )
                        ),
                        working_state.start_date,
                    )
                try:
                    rec.job_tenure = (
                        str(tenure.years)
                        + "年"
                        + str(tenure.months)
                        + "個月"
                        + str(tenure.days)
                        + "天"
                    )
                except:
                    rec.job_tenure = "0年0個月0天"

    def job_tenure_compute(self):
        for rec in self:
            working_state = rec.hr_employee_working_ids.filtered(
                lambda r: r.start_date != False
            ).sorted("start_date", reverse=True)[:1]
            if (
                working_state.change_reason_selection == "resign"
                or working_state.change_reason_selection == "furlough"
            ):
                last_working = rec.hr_employee_working_ids.sorted(
                    "start_date", reverse=True
                )[:2]
                if len(last_working) == 2:
                    tenure = relativedelta(
                        (
                            last_working[0].start_date
                            + relativedelta(
                                years=+rec.past_job_tenure_years,
                                months=+rec.past_job_tenure_months,
                                days=+rec.past_job_tenure_days,
                            )
                        ),
                        last_working[1].start_date,
                    )
                    rec.job_tenure_count = (
                        float(tenure.years * 365 +
                              tenure.months * 30 + tenure.days)
                        / 365
                    )
                else:
                    rec.job_tenure_count = 0
            else:
                if working_state:
                    tenure = relativedelta(
                        (
                            datetime.date.today()
                            + relativedelta(
                                years=+rec.past_job_tenure_years,
                                months=+rec.past_job_tenure_months,
                                days=+rec.past_job_tenure_days,
                            )
                        ),
                        working_state.start_date,
                    )
                    rec.job_tenure_count = (
                        float(tenure.years * 365 +
                              tenure.months * 30 + tenure.days)
                        / 365
                    )
                else:
                    rec.job_tenure_count = 0

    @api.depends("labor_insurance_history_ids")
    def _compute_labor_insurance_gap(self):
        for rec in self:
            # 查詢異動歷程中, 日期最接近系統日期的資料代表已生效資料, 更新勞保級距
            the_last_history = rec.labor_insurance_history_ids.filtered(
                lambda x: x.start_date <= datetime.datetime.now().date()
            ).sorted("start_date", reverse=True)[:1]
            # 如果labor_insurance_history有資料就要更新健保級距
            if the_last_history:
                if the_last_history.change_reason_selection in ["add", "promote"]:
                    rec.hr_labor_insurance_gap_id = (
                        the_last_history.labor_insurance_gap_id.id
                    )
                else:
                    rec.hr_labor_insurance_gap_id = False
            else:
                rec.hr_labor_insurance_gap_id = False

    @api.depends("health_insurance_history_ids")
    def _compute_health_insurance_gap(self):
        for rec in self:
            # 查詢異動歷程中, 日期最接近系統日期的資料代表已生效資料, 更新健保級距
            the_last_history = rec.health_insurance_history_ids.filtered(
                lambda x: x.start_date <= datetime.datetime.now().date()
            ).sorted("start_date", reverse=True)[:1]
            # 如果labor_insurance_history有資料就要更新健保級距
            if the_last_history:
                if the_last_history.change_reason_selection in ["add", "promote"]:
                    rec.hr_health_insurance_gap_id = (
                        the_last_history.health_insurance_gap_id.id
                    )
                else:
                    rec.hr_health_insurance_gap_id = False
            else:
                rec.hr_health_insurance_gap_id = False

    @api.depends("labor_harm_insurance_history_ids")
    def _compute_labor_harm_insurance_gap(self):
        for rec in self:
            # 查詢異動歷程中, 日期最接近系統日期的資料代表已生效資料, 更新勞保級距
            the_last_history = rec.labor_harm_insurance_history_ids.filtered(
                lambda x: x.start_date <= datetime.datetime.now().date()
            ).sorted("start_date", reverse=True)[:1]
            # 如果labor_insurance_history有資料就要更新健保級距
            if the_last_history:
                if the_last_history.change_reason_selection in ["add", "promote"]:
                    rec.labor_harm_insurance_gap_id = (
                        the_last_history.insurance_gap_id.id
                    )
                else:
                    rec.labor_harm_insurance_gap_id = False
            else:
                rec.labor_harm_insurance_gap_id = False

    @api.depends("labor_pension_history_ids")
    def _compute_labor_pension_gap(self):
        for rec in self:
            # 查詢異動歷程中, 日期最接近系統日期的資料代表已生效資料, 更新勞退級距
            the_last_history = rec.labor_pension_history_ids.filtered(
                lambda x: x.start_date <= datetime.datetime.now().date()
            ).sorted("start_date", reverse=True)[:1]
            # 如果labor_insurance_history有資料就要更新健保級距
            if the_last_history:
                if the_last_history.change_reason_selection in [
                    "add",
                    "promote",
                    "self_contribution",
                ]:
                    rec.labor_pension_gap_id = the_last_history.labor_pension_gap_id.id
                else:
                    rec.labor_pension_gap_id = False
            else:
                rec.labor_pension_gap_id = False

    @api.model
    def generate_user_from_employee(self, employee_id):
        employee = self.env['hr.employee'].browse(employee_id)

        if not employee:
            raise UserError("指定的員工不存在！")

        if not employee.employee_number:
            raise UserError("請先設定員工編號後再嘗試。")

        existing_user = self.env["res.users"].search(
            [("employee_id", "=", employee_id)], limit=1
        )
        if not existing_user:
            # Create a new user based on the employee data
            user_vals = {
                "name": employee.name,
                "login": employee.employee_number,
                # You may want to hash this password in a real scenario
                "password": employee.employee_number,
                "company_id": employee.company_id.id,
                "company_ids": [(6, 0, [employee.company_id.id])],
                "employee_ids": [(4, employee.id)],
                "groups_id": [
                    # Assign internal user group
                    (6, 0, [self.env.ref("base.group_user").id])
                ],
            }
            new_user = self.env["res.users"].create(user_vals)
            existing_user = new_user

        employee.user_id = existing_user.id

        return {
            "type": "ir.actions.client",
            "tag": "reload",  # Reload the form to reflect changes
        }

    def is_partial_month(self, date_from=None, date_to=None):
        """判斷是否破月在職"""
        # 月初未到職
        if self.registration_date and self.registration_date > date_from:
            return True
        # 月底已離職
        if self.resignation_date and self.resignation_date < date_to:
            return True
        return False

    def get_partial_month_ratio(self, date_from=None, date_to=None):
        """回傳破月比例，依照中華民國月份天數邏輯計算
        全部都當成30天計算，2月則為28天，以對員工有利方法計算"""
        if not date_from or not date_to:
            return 0.0
        total_days = 30
        # 2月特例
        if date_from.month == 2:
            total_days = 28
        start = max(self.registration_date, date_from)
        end = min(self.resignation_date,
                  date_to) if self.resignation_date else date_to
        work_days = (end - start).days + 1
        ratio = work_days / total_days
        if ratio > 1:
            ratio = 1
        return round(ratio, 10)


class ResPartnerBank(models.Model):
    _name = "res.partner.bank"
    _inherit = "res.partner.bank"

    sub_bank_name = fields.Char("分行")
    book_cover = fields.Many2many(
        "ir.attachment", string="銀行存摺封面", relation="res_partner_bank_book_cover_rel"
    )

    @api.model_create_multi
    def create(self, vals_list):
        records = super(ResPartnerBank, self).create(vals_list)
        for rec in records:
            for attachment in rec.book_cover:
                attachment.sudo().public = True
        return records

    def write(self, vals):
        data = super(ResPartnerBank, self).write(vals)
        for rec in self:
            for attachment in rec.book_cover:
                attachment.sudo().public = True
        return data


class EmergencyContact(models.Model):
    _name = "starrylord.hr.emergency.contact"
    _description = "緊急聯絡人"

    employee_id = fields.Many2one("hr.employee", string="員工")
    name = fields.Char(string="姓名")
    relationship = fields.Char(string="關係")
    phone = fields.Char(string="電話")
