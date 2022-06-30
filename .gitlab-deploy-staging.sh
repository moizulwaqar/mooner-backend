#!/bin/bash
#cat testing.txt
source venv/bin/activate

git pull origin staging

python manage.py makemigrations

python manage.py migrate

sudo systemctl restart gunicorn

exit