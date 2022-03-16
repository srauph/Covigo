from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache

import csv

class MyData:
    dates = []
    amount = []


@login_required
@never_cache
def index(request):
    try:
        recovered_patients_file = open("dashboard/data/recovered_patients.csv", "r")
        reader = csv.DictReader(recovered_patients_file)
        data = list(reader)
        recovered_patients_file.close()
        print(data)
        dates = list(map(lambda x: x['Date'], data))
        numbers = list(map(lambda x: x['Number'], data))
        print(dates)
        print(numbers)

    except FileNotFoundError:
        # TODO: Handle no data yet existing.
        pass
    return render(request, 'dashboard/index.html', {"dates": dates, "numbers": numbers})
