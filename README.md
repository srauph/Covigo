# Covigo

## Pre-requisites:

- Python (3.9/3.10)
- MySQL 8.0

## Quick Setup:

CD to your project root directory (the one containing `manage.py` and install python requirements:
```commandline
cd <project/root/directory>
pip3 install -r requirements.txt
```

Create a text file `/Covigo/.env` (in the same directory that contains `settings.py`); in `.env` insrt this line:
```pycon
DATABASE_PASSWORD="your_mysql_root_password"
```

Run MySQL and create the database
```mysql
mysql -u root -p
CREATE DATABASE Covigo;
exit
```

In your terminal terminal, run these commands:
```
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Covigo should then be running locally and can be accessed at http://127.0.0.1:8000/.

## Detailed Steps:

### Setting up requirements


Once you have the required software installed, open a terminal to the project root directory.
This will be the folder that contains manage.py.

If you'd like, you can run the project from a global Python environment, however we recommend 
using a virtual environment. The exact procedure for setting up a virtual environment
may vary depending on your operating system and Python configuration.

After opening your terminal and (activating your virtualenv), install the Python required packages
by running this command (the exact syntax may vary depending on your OS and Python configuration).

```commandline
 pip3 install -r requirements.txt
 ```

You must have mysql installed and running for the `mysqlclient` package to install successfully.
If installing the requirements fails, please ensure the MySQL service is up and running.

### Creating the database

Once the requirements are installed, you need to create a database called `Covigo`. In your terminal,
enter the MySQL server:

```commandline
mysql -u root -p
```

Enter your root password. You should now be able to run MySQL commands.

```mysql
CREATE DATABASE Covigo;
exit
```

Once this is done, you will have created a database called `Covigo` to be used by the project.

### Configuring Covigo

Once the database is created, you need to create a `.env` file to store Covigo's configuration.
For the development build, you only need to create a Covigo database and configure a MySQL user.

To do so, simply create a file called `.env` in your `Covigo/` folder. **This is not the root 
folder;** rather, this is the folder that contains a file called `settings.py`.

Inside this `.env` file you will need to create environment variables for your MySQL user.

For sake of simplicity we advise you to allow Covigo to use your root MySQL user. Insert this line
into your `.env`, replacing `your_mysql_root_password` with your MySQL server's root password.
```pycon
DATABASE_PASSWORD="your_mysql_root_password"
```

If you would like to use a custom user **instead of the root user**, please ensure that this user 
is granted access to all permissions for the `Covigo` database. You will then need to insert a second 
line to point Covigo to your custom MySQL user, and will need to use that user's password instead of 
the root password.

```pycon
DATABASE_USER="your_mysql_custom_user_username"
DATABASE_PASSWORD="your_mysql_custom_user_password"
```

Whether you use the MySQL root user or a custom user, save the `env` file. You will finally need to
run some configration commands, and then Covigo will be fully set up:

In your terminal, ensuring your working directory is the project's root, run these commands and answer
any questions that are prompted:
```
python manage.py migrate
python manage.py createsuperuser
```

Covigo will then be fully installed and configred. To run the project on a built-in development server,
simply run the command

```commandline
python manage.py runserver
```

Covigo should then be running locally and can be accessed at http://127.0.0.1:8000/.

## Clean installing Covigo

With the exception of the database, which would need to be recreated, you may simply delete the old 
repository files and clone a fresh copy. This is all you need to do regarding files, as this project 
does not store files outside of it's repository folder.

Regarding recreating the database, note that dropping and recreating the database will **deleta all Covigo 
database data** and **is irreversible**.


To recreate the database, enter the MySQL server by running `mysql -u root -p`, and then enter these commands:

```mysql
DROP DATABASE Covigo;
CREATE DATABASE Covigo;
exit
```

The database will be deleted and recreated. Note that you must run `python manage.py migrate` before this
database can be usable again, and that you must run `python manage.py cratesuperuser` to create an account
that you can log in with.
