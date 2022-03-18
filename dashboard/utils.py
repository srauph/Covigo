import csv


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
    print(daily_numbers)
    return {"dates": dates[1:], "numbers": daily_numbers}
