from random import randint
from datetime import datetime
import names


NUM_ROWS = 100
EMPTY_CHANCE_PERCENTAGE = 10
ALLOW_INVALID_ROWS=True

file_name = f"Covigo_{NUM_ROWS}_{datetime.today().date()}_{datetime.now().hour}-{datetime.now().minute}-{datetime.now().second}.csv"

names_list = []

with open(file_name, "w") as f:
    f.write("First Name,Last Name,Email,Phone Number\n")

    for i in range(NUM_ROWS):
        first_name = names.get_first_name()
        last_name = names.get_last_name()
        wrote_email = False
        
        if not ALLOW_INVALID_ROWS:
            while (first_name, last_name) in names_list:
                first_name = names.get_first_name()
                last_name = names.get_last_name()
        
        names_list.append((first_name, last_name))
        
        if not randint(1, 100) <= EMPTY_CHANCE_PERCENTAGE:
            f.write(first_name)
        f.write(",")

        if not randint(1, 100) <= EMPTY_CHANCE_PERCENTAGE:
            f.write(last_name)
        f.write(",")

        if not randint(1, 100) <= EMPTY_CHANCE_PERCENTAGE:
            f.write(f"{first_name}@{last_name}.com")
            wrote_email = True
        f.write(",")

        if not randint(1, 100) <= EMPTY_CHANCE_PERCENTAGE or (not ALLOW_INVALID_ROWS and not wrote_email):
            f.write(str(randint(1000000000,9999999999)))
        f.write("\n")
