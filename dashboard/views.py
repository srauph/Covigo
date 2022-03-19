from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache

from dashboard.utils import fetch_data_from_file, extract_daily_data

data = []


@login_required
@never_cache
def index(request):
    return render(request, 'dashboard/index.html', {
        "data": data,

    })


def fetch_data_from_all_files():
    global data

    confirmed = fetch_data_from_file("dashboard/data/confirmed_cases.csv")
    daily_confirmed = extract_daily_data(confirmed)

    current_positives = fetch_data_from_file("dashboard/data/positive_cases.csv")
    daily_positives = extract_daily_data(current_positives)

    recoveries = fetch_data_from_file("dashboard/data/recovered_cases.csv")
    daily_recoveries = extract_daily_data(recoveries)

    unconfirmed_negative = fetch_data_from_file("dashboard/data/unconfirmed_negative.csv")
    daily_unconfirmed_negative = extract_daily_data(unconfirmed_negative)

    unconfirmed_untested = fetch_data_from_file("dashboard/data/unconfirmed_untested.csv")
    daily_unconfirmed_untested = extract_daily_data(unconfirmed_untested)

    data = {
        "confirmed": confirmed,
        "daily_confirmed": daily_confirmed,
        "current_positives": current_positives,
        "daily_positives": daily_positives,
        "recoveries": recoveries,
        "daily_recoveries": daily_recoveries,
        "unconfirmed_negative": unconfirmed_negative,
        "daily_unconfirmed_negative": daily_unconfirmed_negative,
        "unconfirmed_untested": unconfirmed_untested,
        "daily_unconfirmed_untested": daily_unconfirmed_untested,
    }
