from datetime import date, datetime
from typing import List


def years_to_string(years: List[str]) -> str:
    sorted_years = sorted(set(years))
    if len(sorted_years) > 1:
        first_year = sorted_years[0]
        last_year = sorted_years[-1]
        if sorted_years == [str(y) for y in range(int(first_year), int(last_year)+1)]:
            return '{}-{}'.format(first_year, last_year)
    return ', '.join(y for y in sorted_years)


def year_from_date_string(dt: str) -> str:
    return str(datetime.strptime(dt[:4], '%Y').year)


def year_from_date_object(dt: date) -> str:
    return str(dt.year)


def year_from_date(dt) -> str:
    if isinstance(dt, str):
        return year_from_date_string(dt)
    else:
        return year_from_date_object(dt)


def years_from_date_location_group_field(dlg) -> str:
    years = []
    for dl in dlg:
        if dl.get('date'):
            years.append(year_from_date(dl['date']))
    if years:
        return years_to_string(years)


def years_from_date_time_range_location_group_field(dtrlg) -> str:
    years = []
    for dtrl in dtrlg:
        if dtrl.get('date', {}).get('date'):
            years.append(year_from_date(dtrl['date']['date']))
    if years:
        return years_to_string(years)


def years_list_from_date_range(dr) -> List[str]:
    years = []
    if dr.get('date_from') and dr.get('date_to'):
        date_from = year_from_date(dr['date_from'])
        date_to = year_from_date(dr['date_to'])
        for y in range(int(date_from), int(date_to)+1):
            years.append(str(y))
    elif dr.get('date_from'):
        years.append(year_from_date(dr['date_from']))
    elif dr.get('date_to'):
        years.append(year_from_date(dr['date_to']))
    return years


def years_from_date_range(dr) -> str:
    years = years_list_from_date_range(dr)
    if years:
        return years_to_string(years)


def years_from_date_range_time_range_location_group_field(drtrlg) -> str:
    years = []
    for drtrl in drtrlg:
        if drtrl.get('date'):
            years += years_list_from_date_range(drtrl['date'])
    if years:
        return years_to_string(years)
