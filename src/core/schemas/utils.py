from __future__ import annotations

import operator
from datetime import date, datetime
from itertools import groupby


def years_to_string(years: list[str]) -> str:
    sorted_years = sorted(set(years))
    if len(sorted_years) > 1:
        out = []
        for _k, g in groupby(enumerate(sorted_years), lambda x: int(x[0]) - int(x[1])):
            lst = list(map(operator.itemgetter(1), g))
            if len(lst) > 1:
                out.append(f'{lst[0]}–{lst[-1]}')
            else:
                out.append(lst[0])
        sorted_years = out
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


def years_list_from_date_range(dr) -> list[str]:
    years = []
    if dr.get('date_from') and dr.get('date_to'):
        date_from = year_from_date(dr['date_from'])
        date_to = year_from_date(dr['date_to'])
        for y in range(int(date_from), int(date_to) + 1):
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


def years_from_date_range_location_group_field(drlg) -> str:
    years = []
    for drl in drlg:
        if drl.get('date'):
            years += years_list_from_date_range(drl['date'])
    if years:
        return years_to_string(years)


def years_from_date_range_time_range_location_group_field(drtrlg) -> str:
    return years_from_date_range_location_group_field(drtrlg)
