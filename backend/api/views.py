import csv
from django.conf import settings
from django.core.mail import send_mail
from django.http import HttpResponse
from django.db.models import Sum, Q
from django.utils import timezone
from rest_framework import generics, viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import (User, Room, Device, Action, Stat,
                     Category, Service, DeletionRequest)
from .serializers import (UserRegisterSerializer, UserSerializer,
                          RoomSerializer, DeviceSerializer, ActionSerializer,
                          StatSerializer, CategorySerializer, ServiceSerializer,
                          DeletionRequestSerializer, PasswordChangeSerializer)


# ============================================================
# HELPER : envoi de l'email de validation
# ============================================================
def send_verification_email(user):
    """Envoie l'email de confirmation avec lien de validation."""
    verify_url = f"{settings.FRONTEND_URL}/verify/{user.verification_token}"

    subject = "🏠 Confirmez votre inscription — Maison Intelligente"
    message = f"""Bonjour {user.first_name or user.username},

Bienvenue sur la plateforme Maison Intelligente !

Pour finaliser votre inscription et activer votre compte, cliquez sur le lien
ci-dessous :

    {verify_url}

Vos informations :
- Pseudo : {user.username}
- Rôle attribué : {user.get_role_display()}

Si vous n'êtes pas à l'origine de cette inscription, ignorez ce mail.

— L'équipe Maison Intelligente (CY Tech ING1 2025-2026)
"""

    html_message = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
      <div style="background: linear-gradient(135deg, #26215C, #4f46e5);
                  color: white; padding: 30px; text-align: center; border-radius: 12px 12px 0 0;">
        <h1 style="margin: 0;">🏠 Maison Intelligente</h1>
        <p style="margin: 10px 0 0; opacity: 0.9;">Confirmez votre inscription</p>
      </div>
      <div style="background: white; padding: 30px; border: 1px solid #e5e7eb;
                  border-top: none; border-radius: 0 0 12px 12px;">
        <p>Bonjour <strong>{user.first_name or user.username}</strong>,</p>
        <p>Bienvenue sur la plateforme ! Pour activer votre compte, cliquez sur
           le bouton ci-dessous :</p>
        <p style="text-align: center; margin: 30px 0;">
          <a href="{verify_url}"
             style="background: #4f46e5; color: white; padding: 14px 30px;
                    border-radius: 8px; text-decoration: none; display: inline-block;
                    font-weight: bold;">
            ✔ Activer mon compte
          </a>
        </p>
        <p style="color: #666; font-size: 0.9em;">Ou copiez ce lien dans votre navigateur :</p>
        <p style="background: #f3f4f6; padding: 10px; border-radius: 6px;
                  word-break: break-all; font-size: 0.85em;">{verify_url}</p>
        <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;">
        <p style="color: #666; font-size: 0.85em;">
          <strong>Vos informations :</strong><br>
          Pseudo : {user.username}<br>
          Rôle attribué automatiquement : <strong>{user.get_role_display()}</strong>
        </p>
        <p style="color: #999; font-size: 0.8em; margin-top: 30px;">
          Si vous n'êtes pas à l'origine de cette inscription, ignorez ce mail.<br>
          — Maison Intelligente · CY Tech ING1 2025-2026
        </p>
      </div>
    </div>
    """

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        # On log mais on n'empêche pas l'inscription
        print(f"⚠ Erreur envoi email à {user.email} : {e}")
        return False


# ============================================================
# AUTH
# ============================================================
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        # Envoie le mail de validation
        sent = send_verification_email(user)
        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "email_sent": sent,
            "message": (
                "Inscription réussie ! Un email de validation vous a été envoyé. "
                "Cliquez sur le lien dans l'email pour activer votre compte."
            ),
        }, status=status.HTTP_201_CREATED)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user
        # Bloquer si email pas vérifié
        if not user.email_verified and not user.is_superuser:
            raise serializers.ValidationError(
                "Votre email n'a pas encore été validé. "
                "Cliquez sur le lien dans l'email reçu pour activer votre compte.")
        user.points = (user.points or 0) + 0.25
        user.nb_connexions = (user.nb_connexions or 0) + 1
        user.save()
        Action.objects.create(user=user, action_type="login",
                              description="Connexion à la plateforme")
        ctx = {"request": self.context.get("request")}
        data["user"] = UserSerializer(user, context=ctx).data
        return data


# Import nécessaire pour l'erreur ci-dessus
from rest_framework import serializers


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_password(request):
    s = PasswordChangeSerializer(data=request.data)
    s.is_valid(raise_exception=True)
    if not request.user.check_password(s.validated_data["old_password"]):
        return Response({"detail": "Ancien mot de passe incorrect."}, status=400)
    request.user.set_password(s.validated_data["new_password"])
    request.user.save()
    return Response({"detail": "Mot de passe modifié avec succès."})


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def verify_email(request, token):
    try:
        user = User.objects.get(verification_token=token)
    except User.DoesNotExist:
        return Response({"detail": "Lien de validation invalide ou expiré."},
                        status=400)
    if user.email_verified:
        return Response({"detail": "Cet email est déjà validé.", "already": True})
    user.email_verified = True
    user.save()
    return Response({
        "detail": f"✔ Email validé pour {user.username}. Vous pouvez maintenant vous connecter.",
        "username": user.username,
    })


@api_view(["POST"])
@permission_classes([AllowAny])
def resend_verification(request):
    """Renvoie l'email de validation."""
    email = request.data.get("email", "").lower().strip()
    try:
        user = User.objects.get(email__iexact=email)
    except User.DoesNotExist:
        return Response({"detail": "Aucun compte trouvé avec cet email."}, status=404)
    if user.email_verified:
        return Response({"detail": "Cet email est déjà validé."}, status=400)
    sent = send_verification_email(user)
    return Response({"detail": "Email renvoyé." if sent else "Erreur d'envoi.",
                     "sent": sent})


# ============================================================
# PROFILE
# ============================================================
class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_object(self):
        return self.request.user

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["request"] = self.request
        return ctx


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_users(request):
    users = User.objects.exclude(id=request.user.id)
    return Response(UserSerializer(users, many=True, context={"request": request}).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def set_level(request):
    target = request.data.get("level")
    u = request.user
    if not u.can_set_level(target):
        return Response({"detail": f"Pas assez de points pour le niveau '{target}'."},
                        status=400)
    old = u.level
    u.level = target
    u.save()
    Action.objects.create(user=u, action_type="level_change",
                          description=f"Niveau changé : {old} → {target}")
    return Response(UserSerializer(u, context={"request": request}).data)


# ============================================================
# CATEGORIES / ROOMS
# ============================================================
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"): return [AllowAny()]
        return [IsAuthenticated()]


class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"): return [AllowAny()]
        return [IsAuthenticated()]


# ============================================================
# DEVICES
# ============================================================
class DeviceViewSet(viewsets.ModelViewSet):
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer

    def get_permissions(self):
        if self.action == "list": return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        qs = super().get_queryset()
        p = self.request.query_params
        if p.get("type"):     qs = qs.filter(type=p["type"])
        if p.get("room"):     qs = qs.filter(room_id=p["room"])
        if p.get("category"): qs = qs.filter(category_id=p["category"])
        if p.get("status"):   qs = qs.filter(status=p["status"])
        if p.get("brand"):    qs = qs.filter(brand__icontains=p["brand"])
        if p.get("q"):
            q = p["q"]
            qs = qs.filter(Q(name__icontains=q) | Q(description__icontains=q)
                           | Q(brand__icontains=q))
        return qs

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        u = request.user
        u.points = (u.points or 0) + 0.5
        u.nb_actions = (u.nb_actions or 0) + 1
        u.save()
        Action.objects.create(user=u, action_type="consult", device=instance,
                              description=f"Consultation de {instance.name}")
        return Response(self.get_serializer(instance).data)

    def perform_create(self, serializer):
        # Restriction enfant
        if self.request.user.is_child():
            raise serializers.ValidationError(
                "Les enfants ne peuvent pas ajouter d'objets.")
        device = serializer.save(user=self.request.user)
        self.request.user.nb_actions += 1
        self.request.user.save()
        Action.objects.create(user=self.request.user, action_type="create",
                              device=device, description=f"Création de {device.name}")

    def perform_update(self, serializer):
        if self.request.user.is_child():
            raise serializers.ValidationError(
                "Les enfants ne peuvent pas modifier les objets.")
        device = serializer.save()
        self.request.user.nb_actions += 1
        self.request.user.save()
        Action.objects.create(user=self.request.user, action_type="update",
                              device=device, description=f"Modification de {device.name}")

    def destroy(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return Response(
                {"detail": "Vous devez créer une demande de suppression. "
                           "Seul l'administrateur peut supprimer directement."},
                status=403)
        device = self.get_object()
        Action.objects.create(
            user=request.user, action_type="update",
            description=f"Suppression directe de {device.name} par l'admin")
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=["post"], url_path="repair")
    def repair(self, request, pk=None):
        if request.user.is_child():
            return Response({"detail": "Les enfants ne peuvent pas effectuer de maintenance."},
                            status=403)
        device = self.get_object()
        device.last_maintenance = timezone.now().date()
        device.battery = 100
        device.save()
        Action.objects.create(
            user=request.user, action_type="update", device=device,
            description=f"Maintenance effectuée sur {device.name}")
        return Response(DeviceSerializer(device).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def toggle_device(request, pk):
    try:
        device = Device.objects.get(pk=pk)
    except Device.DoesNotExist:
        return Response({"detail": "Non trouvé"}, status=404)
    # Restriction enfant sur les objets de sécurité
    if not request.user.can_toggle_device(device):
        return Response(
            {"detail": "🔒 Les enfants ne peuvent pas activer/désactiver "
                       "les objets de sécurité (alarme, caméra, porte, détecteur)."},
            status=403)
    device.status = "on" if device.status == "off" else "off"
    device.save()
    request.user.nb_actions += 1
    request.user.save()
    Action.objects.create(user=request.user, action_type="toggle", device=device,
                          description=f"{device.name} → {device.get_status_display()}")
    return Response(DeviceSerializer(device).data)


# ============================================================
# SERVICES
# ============================================================
class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer

    def get_permissions(self):
        if self.action == "list": return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        qs = super().get_queryset()
        p = self.request.query_params
        if p.get("type"):   qs = qs.filter(type=p["type"])
        if p.get("active") is not None and p.get("active") != "":
            qs = qs.filter(active=(p["active"].lower() == "true"))
        if p.get("q"):
            q = p["q"]
            qs = qs.filter(Q(name__icontains=q) | Q(description__icontains=q))
        return qs

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        u = request.user
        u.points = (u.points or 0) + 0.5
        u.nb_actions = (u.nb_actions or 0) + 1
        u.save()
        Action.objects.create(user=u, action_type="consult",
                              description=f"Consultation du service {instance.name}")
        return Response(self.get_serializer(instance).data)


# ============================================================
# DEMANDES DE SUPPRESSION
# ============================================================
class DeletionRequestViewSet(viewsets.ModelViewSet):
    serializer_class = DeletionRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return DeletionRequest.objects.filter(status="pending")
        return DeletionRequest.objects.filter(
            requested_by=self.request.user, status="pending")

    def perform_create(self, serializer):
        if self.request.user.is_child():
            raise serializers.ValidationError(
                "Les enfants ne peuvent pas demander de suppression.")
        dr = serializer.save(requested_by=self.request.user)
        Action.objects.create(
            user=self.request.user, action_type="deletion_request", device=dr.device,
            description=f"Demande de suppression pour {dr.device.name}")

    @action(detail=True, methods=["post"], url_path="approve")
    def approve(self, request, pk=None):
        """Admin approuve : supprime l'objet, marque la demande comme approuvée.
        Bug fix : on capture le nom AVANT toute suppression, et on traite la
        demande dans un ordre qui ne casse pas les références."""
        if not request.user.is_staff:
            return Response({"detail": "Admin uniquement"}, status=403)
        dr = self.get_object()
        if dr.status != "pending":
            return Response({"detail": "Demande déjà traitée"}, status=400)
        device_name = dr.device.name
        device_id = dr.device.id
        # 1. Marquer la demande comme approuvée AVANT de supprimer le device
        #    (sinon le CASCADE supprime aussi la demande et on perd l'info)
        dr.status = "approved"
        dr.resolved_at = timezone.now()
        # On détache le device de la demande pour éviter le CASCADE
        device = dr.device
        dr.save()
        # 2. Créer l'action AVANT de supprimer le device (sans FK device)
        Action.objects.create(
            user=request.user, action_type="update",
            description=f"Suppression de {device_name} (demande approuvée)")
        # 3. Maintenant on peut supprimer le device en toute sécurité
        device.delete()
        return Response({
            "detail": f"✔ Objet « {device_name} » supprimé. Demande traitée.",
            "device_name": device_name,
            "device_id": device_id,
        })

    @action(detail=True, methods=["post"], url_path="reject")
    def reject(self, request, pk=None):
        if not request.user.is_staff:
            return Response({"detail": "Admin uniquement"}, status=403)
        dr = self.get_object()
        if dr.status != "pending":
            return Response({"detail": "Demande déjà traitée"}, status=400)
        device_name = dr.device.name
        dr.status = "rejected"
        dr.resolved_at = timezone.now()
        dr.save()
        return Response({
            "detail": f"✔ Demande pour « {device_name} » refusée. L'objet est conservé.",
            "device_name": device_name,
        })


# ============================================================
# HISTORIQUE / STATS / EXPORTS
# ============================================================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_actions(request):
    return Response(ActionSerializer(
        Action.objects.filter(user=request.user)[:50], many=True).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def global_history(request):
    if request.user.is_child():
        return Response({"detail": "Accès interdit aux enfants."}, status=403)
    qs = Action.objects.filter(device__isnull=False)[:100]
    return Response(ActionSerializer(qs, many=True).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def maintenance_devices(request):
    if request.user.is_child():
        return Response({"detail": "Accès interdit aux enfants."}, status=403)
    to_maintain = [d for d in Device.objects.all() if d.needs_maintenance()]
    return Response(DeviceSerializer(to_maintain, many=True).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def stats_summary(request):
    if request.user.is_child():
        return Response({"detail": "Accès interdit aux enfants."}, status=403)
    devices = Device.objects.all()
    total = Stat.objects.aggregate(t=Sum("consumption"))["t"] or 0
    by_type, by_room = {}, {}
    for d in devices:
        by_type[d.get_type_display()] = by_type.get(d.get_type_display(), 0) + 1
        rn = d.room.name if d.room else "—"
        by_room[rn] = by_room.get(rn, 0) + 1
    return Response({
        "total_devices": devices.count(),
        "active_devices": devices.filter(status="on").count(),
        "total_consumption_kwh": round(total, 2),
        "devices_by_type": by_type,
        "devices_by_room": by_room,
        "maintenance_count": sum(1 for d in devices if d.needs_maintenance()),
        "total_users": User.objects.count(),
        "total_connexions": sum(u.nb_connexions for u in User.objects.all()),
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def export_devices_csv(request):
    if request.user.is_child():
        return Response({"detail": "Accès interdit aux enfants."}, status=403)
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="objets_connectes.csv"'
    response.write("\ufeff")
    w = csv.writer(response, delimiter=";")
    w.writerow(["ID", "Nom", "Type", "Pièce", "Marque", "État",
                "Batterie (%)", "Valeur", "Cible", "Début", "Fin"])
    for d in Device.objects.all():
        w.writerow([d.id, d.name, d.get_type_display(),
                    d.room.name if d.room else "",
                    d.brand, d.get_status_display(),
                    d.battery, d.value, d.target_value,
                    d.start_time or "", d.end_time or ""])
    return response


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def export_stats_csv(request):
    if request.user.is_child():
        return Response({"detail": "Accès interdit aux enfants."}, status=403)
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="consommation.csv"'
    response.write("\ufeff")
    w = csv.writer(response, delimiter=";")
    w.writerow(["Date", "Objet", "Consommation (kWh)"])
    for s in Stat.objects.all():
        w.writerow([s.date, s.device.name, s.consumption])
    return response
