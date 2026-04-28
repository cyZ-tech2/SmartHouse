"""
Liste des emails pré-autorisés à s'inscrire sur SmartHouse.

Pour chaque email :
- "role" : parent ou enfant (attribué automatiquement, pas choisi)
- "require_email_verification" : True → mail de confirmation envoyé,
                                 False → activation directe à la 1ère connexion

Un VISITEUR n'a pas de compte — il navigue librement sans s'inscrire.
"""

ALLOWED_MEMBERS = {
    # Comptes seed (déjà créés et activés)
    "alice@maison.fr":            {"role": "parent", "require_email_verification": False},
    "bob@maison.fr":              {"role": "parent", "require_email_verification": False},
    "charlie@maison.fr":          {"role": "enfant", "require_email_verification": False},
    "demo@maison.fr":             {"role": "parent", "require_email_verification": False},
    "admin@maison.fr":            {"role": "parent", "require_email_verification": False},

    # Email principal de test : MAIL DE CONFIRMATION OBLIGATOIRE
    "acfiren12@gmail.com":        {"role": "parent", "require_email_verification": True},

    # Autres emails autorisés : activation directe à la 1ère connexion (sans mail)
    "famille.dupont@gmail.com":   {"role": "parent", "require_email_verification": False},
    "lucas.dupont@gmail.com":     {"role": "enfant", "require_email_verification": False},
    "marie.martin@gmail.com":     {"role": "parent", "require_email_verification": False},
}


def is_allowed(email: str) -> bool:
    return email.lower().strip() in ALLOWED_MEMBERS


def get_role(email: str) -> str:
    e = email.lower().strip()
    return ALLOWED_MEMBERS.get(e, {}).get("role", "parent")


def requires_email_verification(email: str) -> bool:
    e = email.lower().strip()
    return ALLOWED_MEMBERS.get(e, {}).get("require_email_verification", False)
