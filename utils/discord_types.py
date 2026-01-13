"""
Types personnalisés pour les commandes Discord.

Ce module définit des alias typés réutilisables pour simplifier et centraliser
la déclaration des paramètres dans les commandes slash. Il permet d'améliorer
la lisibilité, la maintenabilité et la compatibilité mobile des interactions.

Exemples :
    - LiteralBool : choix explicite entre "Oui" et "Non", compatible avec les clients Discord mobile.
    - LiteralTriState (à venir) : choix entre "Auto", "Oui", "Non" pour les cas à trois états.

Ces types sont conçus pour être importés dans les cogs et utilisés directement
dans les signatures de commandes Discord.

Auteur : Serge
"""  # noqa: E501

from typing import Literal

# Alias pour un booléen simulé via des choix explicites
LiteralBool = Literal["Oui", "Non"]
