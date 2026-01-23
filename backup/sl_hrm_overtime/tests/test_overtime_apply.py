# 講一年切分成四季, 計算出start_day在哪一季
from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta

# string to date
start_day = datetime.strptime('2024-06-15', '%Y-%m-%d')
# last_day = datetime.strptime('2020-12-31', '%Y-%m-%d')

if start_day.month <= 3:
    season = 1
elif start_day.month <= 6:
    season = 2
elif start_day.month <= 9:
    season = 3
else:
    season = 4
print(season)

first_day = start_day + relativedelta(day=1)

print('first_day ', first_day)
# 取得每一季的第一天
if season == 1:
    season_first_day = first_day + relativedelta(day=1, month=1)
    season_last_day = first_day + relativedelta(day=1, month=4)
    season_last_day -= timedelta(days=1)
elif season == 2:
    season_first_day = first_day + relativedelta(day=1, month=4)
    season_last_day = first_day + relativedelta(day=1, month=7)
    season_last_day -= timedelta(days=1)
elif season == 3:
    season_first_day = first_day + relativedelta(day=1, month=7)
    season_last_day = first_day + relativedelta(day=1, month=9)
    season_last_day -= timedelta(days=1)
else:
    season_first_day = first_day + relativedelta(day=1, month=9)
    season_last_day = first_day + relativedelta(day=31, month=12)
print(season_first_day, season_last_day)
