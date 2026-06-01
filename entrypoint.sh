#!/bin/sh

echo "Demarrage de l'application Django..."

# Wait for MySQL to be ready
echo "Attente de la base de données..."
for i in {1..30}; do
    mysql -h"$MYSQL_HOST" -u"root" -p"$MYSQL_ROOT_PASSWORD" -e "SELECT 1" >/dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "Base de données prête!"
        break
    fi
    echo "Tentative $i/30..."
    sleep 1
done

echo "Application des migrations..."
python manage.py migrate --noinput

echo "Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

echo "Lancement de l'application..."
exec "$@"
