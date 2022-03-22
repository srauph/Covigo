cd /var/django_projects/Covigo/
git pull git@github.com:srauph/Covigo.git
python3.10 -m pip install -r requirements.txt
cd ./tailwind
npm install -D tailwindcss
npx tailwindcss -i ../static/Covigo/css/styles.css -o ../static/Covigo/css/dist/styles.css --minify
cd ..
python3.10 manage.py migrate
python3.10 manage.py collectstatic --noinput
sudo systemctl restart gunicorn.service
systemctl status -l --no-pager nginx.service
systemctl status -l --no-pager gunicorn.service
