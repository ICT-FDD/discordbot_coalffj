# Issues & Solutions

Ce document récapitule les principaux problèmes rencontrés et la manière dont ils ont été résolus, afin de garder un historique à titre pédagogique.

---

## 1) Problèmes de déploiement sur Railway (Poetry vs pip)

- **Symptôme** : Railway tentait d'utiliser Poetry (`poetry install --no-dev`) alors qu'on avait un `requirements.txt` et un `Dockerfile`.
- **Cause** : Railway détectait un `pyproject.toml` ou un autre indicateur, forçant le builder Poetry.
- **Solution** : 
  1. Supprimer/renommer `pyproject.toml`.
  2. Configurer `railway.toml` pour pointer explicitement sur le Dockerfile.
  3. Vérifier les “Service Settings” (Start Command, Builder, etc.) pour enlever toute référence à Poetry.

---

## 2) Privileged Gateway Intents (Message Content)

- **Symptôme** : Avertissement “Privileged message content intent is missing, commands may not work as expected.”
- **Cause** : `intents.message_content = True` n'était pas activé, ou non coché côté Discord Developer Portal.
- **Solution** : 
  1. Ajouter `intents.message_content = True` dans le code.
  2. Aller dans [Discord Developer Portal](https://discord.com/developers/applications) -> Bot -> Activer "Message Content Intent".

---

## 3) Tests d'envoi d'e-mail échouant sur `starttls()`

- **Symptôme** : “AssertionError: Expected 'starttls' to have been called once. Called 0 times.”
- **Cause** : Le `with smtplib.SMTP(...) as server:` renvoie `server = mock_smtp.return_value.__enter__.return_value`, donc l’appel se fait sur l’objet retourné par `__enter__()`.
- **Solution** : 
  1. Dans le test, utiliser `mock_server = mock_smtp.return_value.__enter__.return_value`.
  2. Vérifier `mock_server.starttls.assert_called_once()` plutôt que `mock_smtp.return_value.starttls()`.

---

## 4) Lecture du `.env` dans les tests

- **Symptôme** : Les tests renvoient toujours les mêmes valeurs, même si on modifie `.env`.
- **Cause** : Les tests surchargent `os.environ` dans la méthode `setUp()`.
- **Solution** : 
  1. Soit commenter l'override `os.environ[...] = ...` pour lire vraiment le `.env`,
  2. Soit accepter que les tests utilisent des valeurs fixes pour reproduire un comportement déterministe.

---

## 5) Erreur “TypeError: BotBase.__init__() missing 1 required keyword-only argument: 'intents'”

- **Symptôme** : Les tests d'intégration du bot plantent au moment de créer `commands.Bot(command_prefix="!")`.
- **Cause** : Sur les versions récentes de `discord.py`, `intents` doit être spécifié.
- **Solution** : 
  1. Ajouter `intents=discord.Intents.default()` (ou un Intents personnalisé) lors de l'instantiation du bot.

---

## Autres bugs ou difficultés rencontrées

- **Poetry vs pip** : duplication de configuration.  
- **Permissions Discord** : veiller à ce que le bot ait les droits de lire/écrire dans les canaux ciblés.  
- **Fuseau horaire** : 23h sur Railway est UTC, attention au décalage si on veut 23h heure locale.  

*(Tu peux ajouter d’autres éléments au fur et à mesure.)*
