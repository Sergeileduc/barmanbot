Lister les images docker:
`docker images`

Pour build :

`docker build -t barmanbot-image .`

sur windows :
`docker run -it -v "$PWD\.env:/app/.env" barmanbot-image`

pour fermer, on peut faire :
`docker ps` -> donne la liste des containers

`docker kill IDDUCONTAINER`

AVEC docker-compose (mieux)

```bash
docker-compose up barmanbot
docker-compose stop barmanbot
docker-compose restart barmanbot
```

More :

Si tu veux tester une nouvelle version de ton bot :

- Tu modifies ton code
- Tu fais :

`docker-compose up --build`

- → Ça rebuild l’image et relance le container avec le nouveau code.
- Si tu veux juste redémarrer sans rebuild :

`docker-compose restart`

PARCE QU'ON UTILISE des profils dans docker-compose, il faut faire
`docker-compose --profile prod up --build` (définir le profil à utiliser, quoi)
