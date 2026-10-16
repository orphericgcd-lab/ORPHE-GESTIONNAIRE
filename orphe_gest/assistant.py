import re

from .config import AI_NAME, APP_NAME, CREDIT

POLITE = re.compile(
    r"^(?:orpheric|hey|hi|hello|salut|bonjour|ok|okay|stp|please|s'il te plait|s'il vous plait|"
    r"peux[- ]tu|pourrais[- ]tu|veux[- ]tu|tu peux|je veux que tu|je voudrais que tu|j'aimerais que tu|"
    r"je souhaite que tu|essaie de|can you|could you|would you|will you|i want you to|i'd like you to|"
    r"i would like you to|i need you to|just|now|merci|thanks)\b[\s,]*"
)


def normalize_command_text(text):
    t = text.strip().replace("’", "'")
    n = t.lower()
    while True:
        m = POLITE.match(n)
        if not m:
            break
        t, n = t[m.end():], n[m.end():]
    return t.strip(), n.strip()


def smalltalk(text):
    n = text.strip().lower()
    if re.match(r"^(?:bonjour|salut|hello|hi|hey|coucou)", n):
        return f"Bonjour ! Je suis {AI_NAME}, l’assistant hors ligne de {APP_NAME}.", True
    if re.match(r"^(?:qui es tu|who are you|what is your name)", n):
        return f"Je suis {AI_NAME}, créé par {CREDIT}. Je t’aide à gérer tes fichiers sans internet.", False
    if re.match(r"^(?:merci|thanks)", n):
        return "Avec plaisir ! Que veux-tu faire maintenant ?", False
    return None


def explain_project():
    return (
        "ORPHE - GEST est un gestionnaire de fichiers avec une logique IA locale. "
        "Il peut organiser des fichiers, gérer la corbeille, trier par type, et proposer des actions en français ou en anglais."
    )
