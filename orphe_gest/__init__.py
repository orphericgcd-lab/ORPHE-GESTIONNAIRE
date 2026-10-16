"""Paquet principal du gestionnaire ORPHE - GEST.

Ce package regroupe les éléments de configuration, de logique de fichiers
et d’assistant hors ligne afin de séparer les responsabilités du projet.
"""

from .config import APP_NAME, AI_NAME, CREDIT, LLM_MODEL

__all__ = ["APP_NAME", "AI_NAME", "CREDIT", "LLM_MODEL"]
