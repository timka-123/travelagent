import datetime


def string2date(string_date: str):
    """Переводит стркоу в объект времени

    :argument string_date: дата в формате 12.02.2024 12:00"""
    date, hours = string_date.split()
    day, month, year = list(map(int, date.split(".")))
    hour, minute = list(map(int, hours.split(":")))
    return datetime.datetime(
        year=year, month=month, day=day, hour=hour, minute=minute
    )
