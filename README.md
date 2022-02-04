# Covigo

## Pre-requisites:

- Python
- Nodejs/npm (for tailwind)

## Running the server

Simply run `py manage.py runserver` from the project root directory (the same one with `manage.py`) to start the development server. You will then be able to connect to it locally.

## Running Tailwind

- Switch your directory into the `/tailwind` folder
- Execute tailwindcss to build the `styles.css` file

```
cd tailwind
npx tailwindcss -i ../static/Covigo/css/styles.css -o ../static/Covigo/css/dist/styles.css --watch
```
