import re
import datetime

from dateutil.relativedelta import relativedelta


def to_regexp(line: str):
    # В маске может быть что-то одно из %D %M %Y %F
    # Если в маске присутствует %D значит маска соответствует текущему и предыдущему дню
    # Если в маске присутствует %M значит маска соответствует текущему и предыдущему месяцу
    # Если в маске присутствует %Y или %F значит маска соответствует текущему и предыдущему году
    now = datetime.datetime.now()
    # print(line)
    f = now.strftime('%Y')
    y = now.strftime('%y')
    m = now.strftime('%m')
    d = now.strftime('%d')

    if '%F' in line:
        if '%M' in line or '%D' in line or '%F' in line:
            print("Неправильная комбинация в маске")
            quit(1)
        one_year_ago = now - relativedelta(years=1)
        F = one_year_ago.strftime('%Y')
        tmp_line = re.sub('%F', f"{F}", line)
        line = re.sub('%f', f"{f}", line)
        line = f"({tmp_line}|{line})"
    elif '%Y' in line:
        if '%M' in line or '%D' in line:
            print("Неправильная комбинация в маске")
            quit(1)
        one_year_ago = now - relativedelta(years=1)
        F = one_year_ago.strftime('%Y')
        Y = one_year_ago.strftime('%y')
        tmp_line = re.sub('%Y', f"{Y}", line)
        line = re.sub('%y', f"{y}", line)
        line = f"({tmp_line}|{line})"
    elif '%M' in line:
        if '%D' in line:
            print("Неправильная комбинация в маске")
            quit(1)
        one_month_ago = now - relativedelta(months=1)
        Y = one_month_ago.strftime('%y')
        F = one_month_ago.strftime('%Y')
        M = one_month_ago.strftime('%m')
        tmp_line = re.sub('%y', f"{Y}", line)
        tmp_line = re.sub('%f', f"{F}", tmp_line)
        tmp_line = re.sub('%M', f"{M}", tmp_line)
        line = re.sub('%M', f"{m}", line)
        line = re.sub('%y', f"{y}", line)
        line = re.sub('%f', f"{f}", line)
        line = f"({tmp_line}|{line})"
    elif '%D' in line:
        one_day_ago = now - relativedelta(days=1)
        two_day_ago = now - relativedelta(days=2)
        Y = one_day_ago.strftime('%y')
        F = one_day_ago.strftime('%Y')
        M = one_day_ago.strftime('%m')
        D = one_day_ago.strftime('%d')
        tmp_line = re.sub('%D', f"({D})", line)
        tmp_line = re.sub('%y', f"({Y})", tmp_line)
        tmp_line = re.sub('%f', f"({F})", tmp_line)
        tmp_line = re.sub('%m', f"({M})", tmp_line)

        Y = two_day_ago.strftime('%y')
        F = two_day_ago.strftime('%Y')
        M = two_day_ago.strftime('%m')
        D = two_day_ago.strftime('%d')
        tmp2_line = re.sub('%D', f"({D})", line)
        tmp2_line = re.sub('%y', f"({Y})", tmp2_line)
        tmp2_line = re.sub('%f', f"({F})", tmp2_line)
        tmp2_line = re.sub('%m', f"({M})", tmp2_line)

        line = re.sub('%D', f"({d})", line)
        line = re.sub('%y', f"({y})", line)
        line = re.sub('%f', f"({f})", line)
        line = re.sub('%m', f"({m})", line)
        line = f"({tmp2_line}|{tmp_line}|{line})"
    else:
        line = re.sub('%m', m, line)
        line = re.sub('%y', y, line)
        line = re.sub('%f', f, line)
        line = re.sub('%d', d, line)
    # print(line)
    return line