# SFS – Gestion des notes et vérification des relevés par Blockchain

Plateforme web de gestion des notes pour l'ENSA El Jadida, avec vérification de l'authenticité des relevés de notes grâce à la blockchain Ethereum.

Projet de fin d'année (2ITE, 1ère année) – Année universitaire 2022/2023.

## Principe

L'administrateur génère le relevé de notes d'un étudiant (PDF), puis enregistre son **hash** dans la blockchain via un smart contract. Toute personne externe (entreprise, université…) peut ensuite charger un PDF : le système calcule son hash et vérifie s'il existe dans la blockchain. Si le document a été modifié, la vérification échoue.

## Fonctionnalités

- **Administrateur** : gestion des étudiants et des professeurs (ajout, modification, suppression), génération des relevés, ajout à la blockchain (via MetaMask)
- **Professeur** : saisie des notes par filière, semestre, module et matière
- **Étudiant** : consultation de la fiche d'inscription, des notes et du relevé (une fois généré)
- **Externe** : vérification d'un relevé PDF sans connexion

## Technologies

| Partie | Outils |
|---|---|
| Backend | Python, Flask |
| Frontend | HTML, CSS, JavaScript, Bootstrap |
| Base de données | MySQL (XAMPP) |
| Blockchain | Solidity, Ethereum (réseau de test Goerli), MetaMask |
| Conception | UML (PowerAMC, Lucidchart), méthode SCRUM |

Architecture : MVC.

## Installation

1. Cloner le dépôt :
   ```bash
   git clone https://github.com/farnounef/ProjetFinAnnee.git
   ```
2. Lancer MySQL (XAMPP) et importer la base de données fournie.
3. Déployer le smart contract (`smartcontract.sol`) sur un réseau de test et renseigner son adresse dans la configuration du projet.
4. Installer l'extension MetaMask et la connecter au réseau de test utilisé.
5. Lancer l'application :
   ```bash
   python app4.py
   ```
   Puis ouvrir http://127.0.0.1:5000

> Remarque : le réseau Goerli n'est plus maintenu. Pour relancer le projet, utiliser un autre réseau de test comme Sepolia.

