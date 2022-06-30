#!/bin/bash

source venv/bin/activate

cd mooner-backend/

git pull origin staging

python manage.py makemigrations

python manage.py migrate

sudo systemctl restart gunicorn
