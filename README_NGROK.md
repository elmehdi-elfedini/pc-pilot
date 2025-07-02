Absolument ! Un bon fichier `README.md` est essentiel pour tout projet. Il sert de manuel d'utilisation et de vitrine pour votre travail.

Voici un README complet et professionnel pour votre projet PC-Pilot Pro. Il inclut des instructions claires pour l'installation, l'utilisation locale, et surtout, l'utilisation à distance avec un domaine statique `ngrok`.

Vous pouvez simplement créer un nouveau fichier nommé `README.md` dans le dossier de votre projet et y copier-coller le contenu ci-dessous.

---

# 🚀 PC-Pilot Pro

Contrôlez et surveillez votre PC depuis n'importe où dans le monde, directement depuis le navigateur web de votre téléphone.

> (Note : Vous devriez remplacer `screenshot.png` par une capture d'écran de votre application en action !)
![PC-Pilot Pro Screenshot](screenshot.png)

## ✨ Fonctionnalités

PC-Pilot Pro transforme votre téléphone en un centre de commande complet pour votre ordinateur, offrant une suite d'outils puissants pour la gestion à distance :

*   **📺 Vue de l'écran en direct :** Voyez le bureau de votre PC en temps réel sur votre téléphone.
*   **🖱️ Clic à distance :** Appuyez sur l'image pour envoyer un clic de souris précis.
*   **📊 Tableau de bord système :** Surveillez l'utilisation du CPU, de la RAM, du disque et l'état de la batterie avec des graphiques en direct.
*   **⚙️ Gestionnaire de processus :** Affichez la liste des processus en cours et terminez ceux qui ne répondent pas.
*   **🪟 Gestionnaire de fenêtres :** Affichez les fenêtres ouvertes et fermez-les à distance.
*   **📁 Explorateur de fichiers :** Naviguez dans les fichiers de votre PC, téléchargez des fichiers sur votre téléphone.
*   **📤 Upload de fichiers :** Envoyez des fichiers (photos, documents) de votre téléphone directement sur le bureau de votre PC.
*   **⚡ Contrôles complets :**
    *   **Énergie :** Arrêtez, redémarrez, mettez en veille ou verrouillez votre PC.
    *   **Média :** Contrôlez la lecture (play/pause, suivant/précédent) et le volume.
    *   **Presse-papiers :** Copiez-collez du texte entre votre téléphone et votre PC.
    *   **Et plus :** Ouvrez des URL, tapez du texte à distance, envoyez des notifications, etc.

## 🛠️ Stack Technologique

*   **Backend :** Python, `aiohttp` (serveur web et WebSocket), `mss` (capture d'écran), `psutil` (statistiques système), `pyautogui` (contrôle).
*   **Frontend :** HTML, CSS, JavaScript, Bootstrap 5, Chart.js.
*   **Connectivité :** WebSockets pour la communication en temps réel et **ngrok** pour un accès sécurisé depuis l'extérieur.

## ⚙️ Installation et Configuration

Suivez ces étapes pour mettre en place PC-Pilot Pro.

### 1. Prérequis

*   **Python 3.8+** installé sur votre PC.
*   Un compte **gratuit** sur [ngrok.com](https://ngrok.com).
*   Les fichiers du projet (`server.py`, `index.html`).

### 2. Créer un fichier `requirements.txt`

Créez un fichier nommé `requirements.txt` dans le dossier du projet et collez-y le contenu suivant :

```txt
aiohttp
mss
pygetwindow
pyautogui
psutil
pyperclip
plyer
Pillow
```

### 3. Installer les dépendances Python

Ouvrez un terminal (PowerShell ou Invite de commandes) dans le dossier de votre projet et exécutez la commande suivante pour installer toutes les bibliothèques nécessaires :

```bash
pip install -r requirements.txt
```

### 4. Configurer ngrok pour une adresse fixe (Recommandé)

Pour éviter d'avoir une nouvelle URL à chaque fois, configurez un domaine statique gratuit :
1.  Connectez-vous à votre [tableau de bord ngrok](https://dashboard.ngrok.com/).
2.  Dans le menu de gauche, allez dans **Cloud Edge** -> **Domains**.
3.  Cliquez sur **"+ Create Domain"** pour obtenir votre domaine statique gratuit (ex: `chouette-nom.ngrok-free.app`).
4.  **Copiez cette adresse**, vous en aurez besoin pour lancer l'application.

## ▶️ Comment lancer l'application

Il y a deux façons d'utiliser PC-Pilot Pro : sur votre réseau local ou depuis n'importe où via Internet.

### Méthode 1 : Accès depuis n'importe où (via ngrok)

C'est la méthode la plus puissante.

1.  **Lancez le serveur PC-Pilot Pro :**
    Ouvrez un terminal dans le dossier du projet et exécutez :
    ```bash
    python server.py
    ```
    Le serveur va démarrer et se mettre en attente de connexions.

2.  **Lancez ngrok pour créer le tunnel sécurisé :**
    Ouvrez un **DEUXIÈME** terminal. Exécutez la commande ngrok en utilisant le domaine statique que vous avez réservé. **Remplacez `<votre-domaine-statique-ngrok>` par votre propre domaine.**

    ```bash
    # Exemple de commande (utilisez votre propre domaine !)
    ngrok http --url=wren-cunning-formerly. ngrok-free.app 8765

    ```

3.  **Connectez-vous !**
    Ouvrez le navigateur web sur votre téléphone (ou tout autre appareil) et allez à l'adresse de votre domaine ngrok :
    [`https://wren-cunning-formerly.ngrok-free.app/`](https://wren-cunning-formerly.ngrok-free.app/)

    Vous pouvez maintenant mettre cette adresse en favori. Elle sera toujours la même !

### Méthode 2 : Accès sur votre réseau Wi-Fi local

Utile pour un usage rapide à la maison.

1.  **Lancez le serveur PC-Pilot Pro :**
    ```bash
    python server.py
    ```
2.  Le terminal affichera l'adresse IP locale de votre PC, par exemple `http://192.168.1.10:8765`.
3.  **Connectez-vous :**
    Assurez-vous que votre téléphone est connecté au **même réseau Wi-Fi** que votre PC. Ouvrez le navigateur de votre téléphone et entrez l'adresse affichée dans le terminal.

## 🏗️ Comment ça marche ?

*   **Backend (`server.py`) :** Un serveur `aiohttp` unique gère tout. Il sert le fichier `index.html` lorsqu'on accède à la racine (`/`) et gère la connexion WebSocket bidirectionnelle sur le chemin `/ws`. Une boucle `asyncio` envoie des mises à jour de l'état du PC (`combined_update`) chaque seconde à tous les clients connectés.
*   **Frontend (`index.html`) :** Une application web monopage qui se connecte au serveur via WebSocket. Elle reçoit les données en direct pour mettre à jour l'interface et envoie des commandes (clics, arrêt, etc.) au serveur sous forme de messages JSON.

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.
