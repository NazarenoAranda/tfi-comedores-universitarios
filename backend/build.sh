#!/usr/bin/env bash
# Script de build para Render (se ejecuta en cada despliegue, desde la carpeta backend/).
# Comando en Render:  bash build.sh
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate --no-input
