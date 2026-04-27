"""
Liste des emails pré-autorisés à s'inscrire sur la plateforme.
Seuls les membres de la maison peuvent créer un compte.
Le rôle (parent/enfant) est défini ici, l'utilisateur ne le choisit pas.

Un VISITEUR n'a pas de compte — il navigue librement sans s'inscrire.
"""

ALLOWED_MEMBERS = {
    # Comptes déjà créés (seed)
    "alice@maison.fr":            "parent",
    "bob@maison.fr":              "parent",
    "charlie@maison.fr":          "enfant",
    "demo@maison.fr":             "parent",
    "admin@maison.fr":            "parent",
    # Emails pré-autorisés mais pas encore inscrits
    "acfiren12@gmail.com":        "parent",
    "famille.dupont@gmail.com":   "parent",
    "lucas.dupont@gmail.com":     "enfant",
    "marie.martin@gmail.com":     "parent",
}


def is_allowed(email: str) -> bool:
    """Vérifie si un email est autorisé à s'inscrire."""
    return email.lower().strip() in ALLOWED_MEMBERS


def get_role(email: str) -> str:
    """Renvoie le rôle (parent/enfant) associé à l'email."""
    return ALLOWED_MEMBERS.get(email.lower().strip(), "parent")
