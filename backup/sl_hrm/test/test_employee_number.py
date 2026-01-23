import re
from datetime import datetime
from odoo import fields

# Example date
date_string = "2024/10/31"
# Convert string to datetime object
date = datetime.strptime(date_string, "%Y/%m/%d")

# Get the last two digits of the year
year_last_two_digits = date.strftime("%y")

# Concatenate the year, month, and day in the desired format
date_format_24 = f"{year_last_two_digits}{date.month:02d}{date.day:02d}"

#to lower case

today = fields.date.today()


print(fields.date.today().strftime("%y"))

# 取得KW240005字串中的0005
match = re.search(r'(\d{4})$', 'KW240005')
print(match.group(1))


# email = 'user02@kw.com.tw'
# # 如何取出user02
# print(email.split('@')[0])