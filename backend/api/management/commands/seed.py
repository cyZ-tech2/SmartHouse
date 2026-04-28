import random
from datetime import date, time, datetime, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from api.models import (User, Room, Device, Action, Stat,
                        Category, Service, DeletionRequest)


class Command(BaseCommand):
    help = "Remplit la BDD SmartHouse avec des données initiales."

    def handle(self, *args, **options):
        self.stdout.write("Nettoyage…")
        for m in (DeletionRequest, Stat, Action, Service, Device, Room, Category):
            m.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        # Aussi supprimer l'admin pour un seed propre
        User.objects.filter(username="admin").delete()

        # --- Catégories ---
        cats = {}
        for name, icon, desc in [
            ("Sécurité",       "🔒", "Caméras, alarmes, détecteurs"),
            ("Confort",        "🛋", "Thermostats, climatiseurs, volets"),
            ("Électroménager", "🍽", "Lave-linge, lave-vaisselle, machine à café"),
            ("Divertissement", "📺", "Télé, enceintes"),
            ("Extérieur",      "🌳", "Arrosage, portail, porte garage"),
        ]:
            cats[name] = Category.objects.create(name=name, icon=icon, description=desc)

        # --- Pièces ---
        rooms = [Room.objects.create(name=n, type=t) for n, t in [
            ("Salon", "salon"), ("Chambre parentale", "chambre"),
            ("Chambre enfant", "chambre"), ("Cuisine", "cuisine"),
            ("Salle de bain", "salle_bain"), ("Garage", "garage"),
            ("Jardin", "jardin"),
        ]]

        # --- Utilisateurs ---
        users_data = [
            ("alice",   "alice@maison.fr",   "parent", 35, "expert",        20, "F", "Alice",   "Martin",  date(1990, 5, 12)),
            ("bob",     "bob@maison.fr",     "parent", 37, "avance",        12, "M", "Bob",     "Martin",  date(1988, 3, 8)),
            ("charlie", "charlie@maison.fr", "enfant", 10, "intermediaire",  6, "M", "Charlie", "Martin",  date(2015, 7, 19)),
            ("demo",    "demo@maison.fr",    "parent", 30, "debutant",       0, "N", "Demo",    "User",    date(1994, 1, 1)),
        ]
        users = []
        for u, e, r, age, lvl, pts, gen, fn, ln, dob in users_data:
            user = User.objects.create_user(
                username=u, email=e, password="demo1234",
                age=age, role=r, first_name=fn, last_name=ln)
            user.level, user.points = lvl, pts
            user.gender, user.date_naissance = gen, dob
            user.is_approved = True
            user.email_verified = True
            user.save()
            users.append(user)

        # --- Objets connectés (TOUS à 100% batterie) ---
        devices_data = [
            ("Thermostat Salon",    "thermostat",     rooms[0], cats["Confort"],        "on",  21, 22, "Philips",    time(6,0),  time(23,0)),
            ("Caméra entrée",       "camera",         rooms[0], cats["Sécurité"],       "on",   0,  0, "Hikvision",  None, None),
            ("Lave-linge",          "lave_linge",     rooms[5], cats["Électroménager"], "off",  0,  0, "Bosch",      time(8,0),  time(20,0)),
            ("Lave-vaisselle",      "lave_vaisselle", rooms[3], cats["Électroménager"], "off",  0,  0, "Bosch",      None, None),
            ("Aspirateur robot",    "aspirateur",     rooms[0], cats["Électroménager"], "off",  0,  0, "Roomba",     time(10,0), time(12,0)),
            ("Volet salon",         "volet",          rooms[0], cats["Confort"],        "on",   0,  0, "Somfy",      time(7,0),  time(22,0)),
            ("TV Salon",            "television",     rooms[0], cats["Divertissement"], "off",  0,  0, "Samsung",    None, None),
            ("Climatiseur Chambre", "climatiseur",    rooms[1], cats["Confort"],        "on",  19, 20, "Daikin",     time(22,0), time(6,0)),
            ("Machine à café",      "machine_cafe",   rooms[3], cats["Électroménager"], "on",   0,  0, "Nespresso",  time(6,0),  time(10,0)),
            ("Alarme",              "alarme",         rooms[0], cats["Sécurité"],       "on",   0,  0, "Verisure",   None, None),
            ("Arrosage jardin",     "arrosage",       rooms[6], cats["Extérieur"],      "off",  0,  0, "Gardena",    time(6,0),  time(7,0)),
            ("Porte garage",        "porte",          rooms[5], cats["Extérieur"],      "off",  0,  0, "Sommer",     None, None),
            ("Enceinte Salon",      "enceinte",       rooms[0], cats["Divertissement"], "off",  0,  0, "Sonos",      None, None),
            ("Détecteur Entrée",    "detecteur",      rooms[0], cats["Sécurité"],       "on",   0,  0, "Netatmo",    None, None),
            ("Thermostat Chambre",  "thermostat",     rooms[1], cats["Confort"],        "on",  19, 20, "Nest",       None, None),
        ]
        devices = []
        for name, t, room, cat, st, val, tgt, brand, start, end in devices_data:
            d = Device.objects.create(
                name=name, type=t, room=room, category=cat, status=st,
                battery=100,
                value=val, target_value=tgt, brand=brand,
                start_time=start, end_time=end,
                user=random.choice(users[:2]),
                description=f"{name} — marque {brand}. Connecté en Wi-Fi.",
                last_maintenance=date(2025, 10, 15),
            )
            devices.append(d)

        # --- 2 objets avec maintenance ancienne ---
        devices[4].last_maintenance = date(2024, 1, 15)
        devices[4].save()
        devices[10].last_maintenance = date(2023, 8, 10)
        devices[10].save()

        # --- Services ---
        services = [
            ("Suivi consommation électrique",
             "Visualise la consommation kWh de tous tes appareils en temps réel.",
             "energie", devices[2]),
            ("Alarme intrusion",
             "Notification instantanée dès qu'un mouvement suspect est détecté.",
             "securite", devices[9]),
            ("Surveillance vidéo",
             "Accède aux flux des caméras à distance depuis ton téléphone.",
             "securite", devices[1]),
            ("Mode nuit automatique",
             "Baisse le chauffage à 19°C et ferme les volets à 22h.",
             "confort", devices[0]),
            ("Planning machine à café",
             "Café prêt chaque matin à 6h30 du lundi au vendredi.",
             "confort", devices[8]),
            ("Streaming musical multiroom",
             "Diffusion de musique dans toutes les pièces depuis ton téléphone.",
             "divertissement", devices[12]),
            ("Rapport énergétique hebdomadaire",
             "Bilan hebdo envoyé chaque dimanche par email.",
             "energie", None),
            ("Arrosage intelligent",
             "Programmation automatique selon la météo.",
             "confort", devices[10]),
            ("Cinéma à la maison",
             "Lance la TV, baisse les volets, éteint la lumière en un clic.",
             "divertissement", devices[6]),
            ("Détection de fuite",
             "Alerte en cas d'anomalie de consommation d'eau.",
             "securite", None),
        ]
        for n, d, t, dev in services:
            Service.objects.create(name=n, description=d, type=t, related_device=dev)

        # --- Stats de consommation ---
        for d in devices:
            for _ in range(7):
                Stat.objects.create(device=d,
                                    consumption=round(random.uniform(0.1, 3.5), 2))

        # --- Historique varié : connexions étalées sur plusieurs jours/heures ---
        # Pour chaque user, génère des connexions à des moments réalistes
        # (matin, midi, soir, sur les 3 dernières semaines)
        now = timezone.now()
        # Profils différents par utilisateur
        user_profiles = {
            users[0].id: 25,  # alice : très active
            users[1].id: 18,  # bob : assez active
            users[2].id: 8,   # charlie : enfant, moins de connexions
            users[3].id: 4,   # demo : peu utilisé
        }

        # Heures réalistes (matin, midi, soir)
        realistic_hours = [
            (7, 30), (8, 15), (12, 5), (12, 45),
            (18, 20), (19, 30), (20, 45), (21, 15), (22, 0),
        ]

        for user in users:
            n_logins = user_profiles[user.id]
            user_actions = []
            for _ in range(n_logins):
                # Date aléatoire dans les 21 derniers jours
                days_ago = random.randint(0, 20)
                hour, minute = random.choice(realistic_hours)
                # Petite variation aléatoire
                minute_offset = random.randint(-15, 15)
                date_login = now - timedelta(days=days_ago)
                date_login = date_login.replace(
                    hour=hour, minute=max(0, min(59, minute + minute_offset)),
                    second=random.randint(0, 59), microsecond=0)
                user_actions.append(date_login)

            # Tri pour générer dans l'ordre chronologique (plus récent en dernier)
            user_actions.sort()

            for d_login in user_actions:
                a = Action.objects.create(
                    user=user,
                    action_type="login",
                    description="Connexion à la plateforme",
                )
                # auto_now_add empêche de fixer la date à la création :
                # on l'écrase via update juste après
                Action.objects.filter(pk=a.pk).update(date=d_login)

            # Quelques consultations aussi pour réalisme
            for _ in range(random.randint(3, 8)):
                days_ago = random.randint(0, 14)
                hour, minute = random.choice(realistic_hours)
                date_consult = now - timedelta(days=days_ago)
                date_consult = date_consult.replace(
                    hour=hour, minute=minute,
                    second=random.randint(0, 59), microsecond=0)
                device = random.choice(devices)
                a = Action.objects.create(
                    user=user,
                    action_type="consult",
                    device=device,
                    description=f"Consultation de {device.name}",
                )
                Action.objects.filter(pk=a.pk).update(date=date_consult)

            # Mettre à jour le compteur nb_connexions du user
            user.nb_connexions = n_logins
            user.nb_actions = n_logins + random.randint(3, 8)
            user.save()

        # --- Demande de suppression de démo ---
        DeletionRequest.objects.create(
            device=devices[4],
            requested_by=users[1],
            reason="Batterie en fin de vie, on va le remplacer.",
            status="pending",
        )

        # --- Superuser admin ---
        User.objects.create_superuser(
            username="admin", email="admin@maison.fr",
            password="admin1234", role="parent",
            level="expert", points=100, age=40,
            first_name="Admin", last_name="System",
            is_approved=True, email_verified=True)

        self.stdout.write(self.style.SUCCESS("✔ Données SmartHouse générées !"))
        self.stdout.write(" Tous les objets ont 100% de batterie au départ.")
        self.stdout.write(" 2 objets ont une maintenance ancienne (démo Maintenance).")
        self.stdout.write(" Connexions étalées sur 21 jours, à des heures réalistes.")
        self.stdout.write("")
        self.stdout.write(" Comptes : alice / bob / charlie / demo (mdp : demo1234)")
        self.stdout.write(" Admin   : admin / admin1234")
        self.stdout.write("")
        self.stdout.write(" Emails pré-autorisés à s'inscrire :")
        self.stdout.write("   - acfiren12@gmail.com (parent) → MAIL DE CONFIRMATION")
        self.stdout.write("   - famille.dupont@gmail.com (parent) → activation auto")
        self.stdout.write("   - lucas.dupont@gmail.com (enfant) → activation auto")
        self.stdout.write("   - marie.martin@gmail.com (parent) → activation auto")
