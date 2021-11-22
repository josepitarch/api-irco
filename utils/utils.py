import datetime
from datetime import date
from datetime import timedelta

def interval_of_dates(name_date, today):
        date_ini, date_end = "", ""
        
        if name_date == "Monday":
            f1 = today
            f2 = today + timedelta(days=6)
            date_ini = str(f1) + " 00:00:00"
            date_end = str(f2) + " 23:59:59"
        elif name_date == "Tuesday":
            f1 = today + timedelta(days=-1)
            f2 = today + timedelta(days=5)
            date_ini = str(f1) + " 00:00:00"
            date_end = str(f2) + " 23:59:59"
        elif name_date == "Wednesday":
            f1 = today + timedelta(days=-2)
            f2 = today + timedelta(days=4)
            date_ini = str(f1) + " 00:00:00"
            date_end = str(f2) + " 23:59:59"
        elif name_date == "Thursday":
            f1 = today + timedelta(days=-3)
            f2 = today + timedelta(days=3)
            date_ini = str(f1) + " 00:00:00"
            date_end = str(f2) + " 23:59:59"
        elif name_date == "Friday":
            f1 = today + timedelta(days=-4)
            f2 = today + timedelta(days=2)
            date_ini = str(f1) + " 00:00:00"
            date_end = str(f2) + " 23:59:59"
        elif name_date == "Saturday":
            f1 = today + timedelta(days=-5)
            f2 = today + timedelta(days=1)
            date_ini = str(f1) + " 00:00:00"
            date_end = str(f2) + " 23:59:59"
        elif name_date == "Sunday":
            f1 = today + timedelta(days=-6)
            f2 = today
            date_ini = str(f1) + " 00:00:00"
            date_end = str(f2) + " 23:59:59"

        return date_ini, date_end

def interval_op_future(name_date, today):
    date_ini, date_end = "", ""

    if name_date == "Monday":
        f1 = today
        f2 = today + timedelta(days=30)
        date_ini += str(f1) + " 00:00:00"
        date_end += str(f2) + " 23:59:59"
    elif name_date == "Tuesday":
        f1 = today + timedelta(days=-1)
        f2 = today + timedelta(days=29)
        date_ini += str(f1) + " 00:00:00"
        date_end += str(f2) + " 23:59:59"
    elif name_date == "Wednesday":
        f1 = today + timedelta(days=-2)
        f2 = today + timedelta(days=28)
        date_ini += str(f1) + " 00:00:00"
        date_end += str(f2) + " 23:59:59"
    elif name_date == "Thursday":
        f1 = today + timedelta(days=-3)
        f2 = today + timedelta(days=27)
        date_ini += str(f1) + " 00:00:00"
        date_end += str(f2) + " 23:59:59"
    elif name_date == "Friday":
        f1 = today + timedelta(days=-4)
        f2 = today + timedelta(days=26)
        date_ini += str(f1) + " 00:00:00"
        date_end += str(f2) + " 23:59:59"
    elif name_date == "Saturday":
        f1 = today + timedelta(days=-5)
        f2 = today + timedelta(days=25)
        date_ini += str(f1) + " 00:00:00"
        date_end += str(f2) + " 23:59:59"
    elif name_date == "Sunday":
        f1 = today + timedelta(days=-6)
        f2 = today + timedelta(days=24)
        date_ini += str(f1) + " 00:00:00"
        date_end += str(f2) + " 23:59:59"

    return date_ini, date_end