import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path

from .config import APP_DIR


RECALL_PHRASES = (
    "tu te souviens", "souviens toi", "rappelle moi", "historique", "qu est ce qu on a fait",
    "qu est ce que tu as fait", "qu est ce que j ai fait", "qu est ce que je t ai demande",
    "qu est ce que j ai demande", "what did we do", "what did you do", "what did i do", "what did i ask",
    "what have we done", "remember",
)
STOP_WORDS = {
    "avec", "dans", "pour", "que", "qui", "quoi", "quand", "comment", "faire", "fait", "fais",
    "this", "that", "what", "when", "where", "which", "have", "with", "from", "about", "were",
}


def _normalize(text):
    text = unicodedata.normalize("NFD", str(text).lower())
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def _tokens(text):
    return {word for word in _normalize(text).split() if len(word) > 2 and word not in STOP_WORDS}


class AssistantMemory:
    """Keeps the current conversation in memory and persists file-manager actions."""

    def __init__(self, path=None):
        self.path = Path(path) if path else APP_DIR / "assistant_memory.json"
        self.conversations = []
        self.actions = []
        self._load()

    def _load(self):
        try:
            with self.path.open(encoding="utf-8") as stream:
                data = json.load(stream)
            if isinstance(data, dict):
                self.conversations = []
                self.actions = [item for item in data.get("actions", []) if isinstance(item, dict)]
        except (OSError, ValueError, TypeError):
            self.conversations, self.actions = [], []

    def _save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_name(self.path.name + ".tmp")
        with temporary.open("w", encoding="utf-8") as stream:
            json.dump({"actions": self.actions}, stream,
                      ensure_ascii=False, indent=1)
        temporary.replace(self.path)

    def record_exchange(self, user, assistant):
        if not str(user).strip():
            return
        self.conversations.append({
            "time": datetime.now().isoformat(timespec="seconds"),
            "user": str(user)[:5000],
            "assistant": str(assistant)[:5000],
        })

    def clear_conversations(self):
        self.conversations = []
        self._save()

    @staticmethod
    def _safe_value(value, depth=0):
        if depth > 2:
            return "..."
        if isinstance(value, dict):
            return {str(key): AssistantMemory._safe_value(item, depth + 1)
                    for key, item in value.items() if str(key).lower() != "content"}
        if isinstance(value, (list, tuple)):
            return [AssistantMemory._safe_value(item, depth + 1) for item in value[:20]]
        if isinstance(value, str):
            return value[:300]
        if isinstance(value, (bool, int, float)) or value is None:
            return value
        return str(value)[:300]

    def record_action(self, name, args, success, result):
        self.actions.append({
            "time": datetime.now().isoformat(timespec="seconds"),
            "tool": str(name),
            "args": self._safe_value(args or {}),
            "success": bool(success),
            "result": str(result)[:1000],
        })
        self._save()

    def chat_entries(self, limit=8):
        entries = []
        for item in self.conversations[-limit:]:
            user = str(item.get("user", "")).strip()
            assistant = str(item.get("assistant", "")).strip()
            if user:
                entries.append(("user", user))
            if assistant:
                entries.append(("ai", assistant))
        return entries

    def has_data(self):
        return bool(self.conversations or self.actions)

    def clear(self):
        self.conversations, self.actions = [], []
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass

    @staticmethod
    def _format_action(item):
        args = json.dumps(item.get("args", {}), ensure_ascii=False)
        status = "réussie" if item.get("success") else "échouée"
        result = str(item.get("result", ""))[:500]
        return f"{item.get('tool', 'action')} {args} ({status}) : {result}"

    def context(self, query=""):
        lines = []
        recent_conversations = self.conversations[-5:]
        recent_actions = self.actions[-10:]
        if recent_conversations:
            lines.append("Échanges récents :")
            for item in recent_conversations:
                lines.append(f"Utilisateur : {str(item.get('user', ''))[:700]}")
                lines.append(f"Assistant : {str(item.get('assistant', ''))[:700]}")
        if recent_actions:
            lines.append("Actions récentes dans le gestionnaire :")
            lines.extend(f"- {self._format_action(item)}" for item in recent_actions)

        keywords = _tokens(query)
        if keywords:
            recent_conversation_ids = {id(item) for item in recent_conversations}
            matches = []
            for item in self.conversations:
                if id(item) in recent_conversation_ids:
                    continue
                text = f"{item.get('user', '')} {item.get('assistant', '')}"
                score = sum(word in _normalize(text) for word in keywords)
                if score:
                    matches.append((score, item.get("time", ""), "Échange antérieur : "
                                    f"utilisateur={str(item.get('user', ''))[:500]} ; "
                                    f"assistant={str(item.get('assistant', ''))[:500]}"))
            recent_action_ids = {id(item) for item in recent_actions}
            for item in self.actions:
                if id(item) in recent_action_ids:
                    continue
                text = self._format_action(item)
                score = sum(word in _normalize(text) for word in keywords)
                if score:
                    matches.append((score, item.get("time", ""), "Action antérieure : " + text[:1000]))
            matches.sort(key=lambda match: (match[0], match[1]), reverse=True)
            if matches:
                lines.append("Souvenirs pertinents :")
                lines.extend(f"- {match[2]}" for match in matches[:4])
        return "\n".join(lines)[:7000]

    def recall(self, query):
        normalized = _normalize(query)
        if not any(phrase in normalized for phrase in RECALL_PHRASES):
            return None
        if not self.has_data():
            return "Je n'ai pas encore d'historique enregistré."

        events = []
        for item in self.conversations[-5:]:
            events.append((item.get("time", ""),
                           f"Discussion : tu as dit « {str(item.get('user', ''))[:220]} » ; "
                           f"j'ai répondu « {str(item.get('assistant', ''))[:220]} »."))
        for item in self.actions[-8:]:
            events.append((item.get("time", ""), "Action : " + self._format_action(item)))
        events.sort(key=lambda event: event[0])
        return "Voici ce que j'ai gardé en mémoire :\n" + "\n".join(
            f"- {text}" for _time, text in events[-8:]
        )