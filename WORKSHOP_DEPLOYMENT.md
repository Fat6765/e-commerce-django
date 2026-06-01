Atelier pratique — Déploiement Django avec Docker, MySQL et Dokploy
===============================================================

Module : Développement Web avec Django — Année 2025–2026

Objectif
--------
Ce document regroupe, pas à pas, les étapes de l'atelier à joindre au projet.
Il explique comment conteneuriser l'application Django, lancer MySQL, construire
et publier une image Docker, puis déployer via Dokploy.

Prérequis
---------
- Compte GitHub (projet source)
- Compte Docker Hub (pour pousser l'image)
- Accès Dokploy et port attribué par l'enseignant
- Docker & Docker Compose installés localement

Fichiers clés du projet
-----------------------
- `Dockerfile`         : instructions pour construire l'image web
- `docker-compose.yaml`: orchestration locale (web + db)
- `.env`               : variables d'environnement (ne pas committer en clair)
- `entrypoint.sh`      : script d'initialisation (migrations + collectstatic)
- `requirements.txt`   : dépendances Python

Étapes détaillées (adaptées à ce projet)
----------------------------------------

1) Créer un fichier `.env` à la racine (exemple minimal) :

```
DJANGO_SECRET_KEY=change-this-secret-key
DJANGO_DEBUG=1
DJANGO_ALLOWED_HOSTS=*
MYSQL_ROOT_PASSWORD=root
MYSQL_DATABASE=DB_ECOMMERCE
MYSQL_USER=django
MYSQL_PASSWORD=django
MYSQL_HOST=db
MYSQL_PORT=3306
```

2) Vérifier `requirements.txt` (Django, mysqlclient, gunicorn, whitenoise, Pillow).

3) Dockerfile (déjà fourni) — points importants :
- utiliser `python:3.12-slim` ou une image adaptée;
- installer `default-libmysqlclient-dev` et dépendances de compilation;
- copier `requirements.txt` et installer les paquets;
- copier le projet, rendre `entrypoint.sh` exécutable;
- `ENTRYPOINT ["/entrypoint.sh"]` et `CMD` lance Gunicorn.

4) `entrypoint.sh` (existant) :
- attendre la base MySQL (healthcheck);
- exécuter `python manage.py migrate --noinput`;
- exécuter `python manage.py collectstatic --noinput`;
- exécuter le CMD (Gunicorn).

5) `docker-compose.yaml` (local) :
- service `db`: image MySQL (8.0), variables d'environnement, volume `db_data`, healthcheck;
- service `web`: build context `.` ou image (pour Dokploy on utilisera l'image publiée), `env_file: - .env`, ports `8000:8000`, dépend de `db` (condition de health).

6) Lancement local (tests) :

```
docker compose up -d --build
docker compose ps
docker compose logs -f web
```

Vérifier : http://localhost:8000/products/

7) Créer les migrations si nécessaire :

```
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate
```

8) Créer un superuser :

```
docker compose exec web python manage.py createsuperuser
```

9) Construire l'image finale et tagger pour Docker Hub :

```
docker build -t <dockerhub-username>/<repo-name>:v1 .
```

10) Se connecter à Docker Hub et pousser :

```
docker login
docker push <dockerhub-username>/<repo-name>:v1
```

11) Dokploy — préparation :
- Créer un projet sur Dokploy (compte fourni par l'enseignant);
- Dans le projet : Create Service -> Docker Compose;
- Coller le `docker-compose.yml` adapté : remplacer `web.build` par `web.image: <username>/<repo-name>:v1` et remplacer le port interne par le port qui vous est attribué (ex. `"8001:8000"`).
- Ajouter les variables d'environnement dans Dokploy (mêmes que dans `.env`).

12) Lancer le déploiement sur Dokploy (Deploy) et surveiller les logs :

- Containers -> web -> Logs

13) Vérifier l'application depuis l'URL fournie :

```
http://<IP_VM>:<PORT>/products/
```

Bonnes pratiques & erreurs fréquentes
-----------------------------------
- Ne pas utiliser `container_name` dans `docker-compose.yml` (environnements partagés).
- Ne pas exposer MySQL publiquement (ne pas faire `3306:3306`).
- Si `Access denied for user django` : supprimer le volume MySQL (si possible) et redéployer avec les bonnes variables d'env.
- Si `Table does not exist` : vérifier que les fichiers de migration existaient avant la construction, exécuter `makemigrations` puis `migrate`.

Consignes de remise
-------------------
Chaque étudiant doit fournir :
- le lien GitHub du projet;
- le nom de l'image Docker Hub utilisée (ex. `username/projet:v1`);
- `Dockerfile`, `docker-compose.yml`, `.env` (exemple);
- capture d'écran du test local `docker compose up`;
- capture d'écran du déploiement Dokploy et des containers en fonctionnement;
- URL finale accessible.

Fichier ajouté
--------------
Ce document a été ajouté automatiquement au projet sous le nom `WORKSHOP_DEPLOYMENT.md`.

Bonne réussite pour l'atelier — dites‑moi si vous voulez :
- que je génère des captures d'écran headless des pages (utilisant `curl`/`playwright`);
- que je crée une branche `workshop` et y ouvre une PR avec ces documents et exemples;
- que j'ajoute un script `deploy.sh` pour automatiser build/push.
