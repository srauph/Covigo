from random import randint
from datetime import datetime
import names


NUM_ROWS = 200
EMPTY_CHANCE_PERCENTAGE = 10
file_name = f"Covigo_{NUM_ROWS}_{datetime.today().date()}_{datetime.now().hour}-{datetime.now().minute}-{datetime.now().second}.csv"


with open(file_name, "w") as f:
    f.write("First Name,Last Name,Email,Phone Number\n")

    for i in range(NUM_ROWS):
        first_name = names.get_first_name()
        last_name = names.get_last_name()
        
        if not randint(1, 100) <= EMPTY_CHANCE_PERCENTAGE:
            f.write(first_name)
        f.write(",")

        if not randint(1, 100) <= EMPTY_CHANCE_PERCENTAGE:
            f.write(last_name)
        f.write(",")

        if not randint(1, 100) <= EMPTY_CHANCE_PERCENTAGE:
            f.write(f"{first_name}@{last_name}.com")
        f.write(",")

        if not randint(1, 100) <= EMPTY_CHANCE_PERCENTAGE:
            f.write(str(randint(1000000000,9999999999)))
        f.write("\n")
