from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache

import csv


@login_required
@never_cache
def index(request):
    recoveries = fetch_data_from_file("dashboard/data/recovered_patients.csv")
    daily_recoveries = extract_daily_data(recoveries)
    cumulative_positives = fetch_data_from_file("dashboard/data/recovered_patients.csv")

    return render(request, 'dashboard/index.html', {
        "recoveries": recoveries,
        "daily_recoveries": daily_recoveries,
        # "recoveries": {"dates": recoveries[0], "numbers": recoveries[1]},
        # "recoveries": {"dates": recoveries[0], "numbers": recoveries[1]},
        # "recoveries": {"dates": recoveries[0], "numbers": recoveries[1]},
        # "recoveries": {"dates": recoveries[0], "numbers": recoveries[1]},
        # "recoveries": {"dates": recoveries[0], "numbers": recoveries[1]},
        # "recoveries": {"dates": recoveries[0], "numbers": recoveries[1]},
        # "recoveries": {"dates": recoveries[0], "numbers": recoveries[1]},
    })


def fetch_data_from_file(file_name, date_header_name="Date", number_header_name="Number"):
    try:
        opened_file = open(file_name, "r")
        reader = csv.DictReader(opened_file)
        data = list(reader)
        opened_file.close()
        dates = list(map(lambda x: x[date_header_name], data))
        numbers = list(map(lambda x: x[number_header_name], data))

        return {"dates": dates, "numbers": numbers}

    except FileNotFoundError:
        # TODO: Handle no data yet existing.
        pass


def extract_daily_data(data):
    dates = data["dates"]
    cumulative_numbers = data["numbers"]
    daily_numbers = list(map(lambda n1, n2: str(int(n2)-int(n1)), cumulative_numbers[:-1], cumulative_numbers[1:]))
    return {"dates": dates[1:], "numbers": daily_numbers}
