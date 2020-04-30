import datetime as dt
from django.shortcuts import render

def year(request):
    current_year = dt.datetime.now().date().year
    return {
        'year' : current_year
    }