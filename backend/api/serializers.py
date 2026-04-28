from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import (User, Room, Device, Action, Stat,
                     Category, Service, DeletionRequest)
from .allowed_members import is_allowed, get_role, requires_email_verification


class UserRegisterSerializer(serializers.ModelSerializer):
    """Inscription : le rôle est déterminé par l'email pré-autorisé,
    pas choisi par l'utilisateur. L'envoi du mail dépend du flag de l'email."""
    password = serializers.CharField(write_only=True, required=True,
                                     validators=[validate_password])

    class Meta:
        model = User
        fields = ("id", "username", "email", "password",
                  "first_name", "last_name",
                  "age", "gender", "date_naissance")

    def validate_email(self, value):
        v = value.lower().strip()
        if not is_allowed(v):
            raise serializers.ValidationError(
                "Cet email n'est pas autorisé. Seuls les membres de la maison "
                "peuvent s'inscrire. Contactez l'administrateur si vous pensez "
                "que c'est une erreur.")
        if User.objects.filter(email__iexact=v).exists():
            raise serializers.ValidationError(
                "Un compte existe déjà avec cet email.")
        return v

    def create(self, validated_data):
        pwd = validated_data.pop("password")
        email = validated_data["email"]
        role = get_role(email)
        # email_verified = False uniquement si l'email exige un mail
        # Sinon, le compte sera auto-activé à la 1ère connexion
        needs_mail = requires_email_verification(email)
        user = User.objects.create_user(
            password=pwd,
            role=role,
            email_verified=False,  # toujours False à la création
            is_approved=True,
            **validated_data,
        )
        # On stocke le flag dans un attribut transient pour la vue
        user._needs_mail = needs_mail
        return user


class UserSerializer(serializers.ModelSerializer):
    max_level = serializers.CharField(source="max_level_allowed", read_only=True)
    photo_url = serializers.SerializerMethodField()
    is_child = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name",
                  "age", "role", "gender", "date_naissance",
                  "photo", "photo_url",
                  "level", "points", "max_level",
                  "nb_connexions", "nb_actions",
                  "is_approved", "email_verified", "is_staff", "is_child")
        # Le rôle est read_only : impossible de devenir parent en modifiant son profil
        read_only_fields = ("level", "points", "nb_connexions", "nb_actions",
                            "is_approved", "email_verified", "max_level",
                            "is_staff", "role", "is_child")

    def get_photo_url(self, obj):
        request = self.context.get("request")
        if obj.photo and request:
            return request.build_absolute_uri(obj.photo.url)
        return None


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = "__all__"


class DeviceSerializer(serializers.ModelSerializer):
    room_name = serializers.CharField(source="room.name", read_only=True)
    type_display = serializers.CharField(source="get_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)
    needs_maintenance = serializers.BooleanField(read_only=True)
    is_security = serializers.SerializerMethodField()

    class Meta:
        model = Device
        fields = ("id", "name", "type", "type_display", "description",
                  "category", "category_name",
                  "room", "room_name",
                  "status", "status_display",
                  "battery", "value", "target_value", "brand",
                  "start_time", "end_time", "last_maintenance",
                  "needs_maintenance", "is_security",
                  "user", "created_at")
        read_only_fields = ("created_at", "user")

    def get_is_security(self, obj):
        return obj.type in User.SECURITY_DEVICE_TYPES


class ServiceSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source="get_type_display", read_only=True)
    related_device_name = serializers.CharField(source="related_device.name", read_only=True)

    class Meta:
        model = Service
        fields = ("id", "name", "description", "type", "type_display",
                  "related_device", "related_device_name", "active", "created_at")


class ActionSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.username", read_only=True)
    device_name = serializers.CharField(source="device.name", read_only=True)
    action_type_display = serializers.CharField(source="get_action_type_display", read_only=True)

    class Meta:
        model = Action
        fields = ("id", "user", "user_name", "action_type", "action_type_display",
                  "description", "device", "device_name", "date")


class StatSerializer(serializers.ModelSerializer):
    device_name = serializers.CharField(source="device.name", read_only=True)

    class Meta:
        model = Stat
        fields = ("id", "device", "device_name", "consumption", "date")


class DeletionRequestSerializer(serializers.ModelSerializer):
    device_name = serializers.CharField(source="device.name", read_only=True)
    requested_by_name = serializers.CharField(source="requested_by.username", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = DeletionRequest
        fields = ("id", "device", "device_name",
                  "requested_by", "requested_by_name",
                  "reason", "status", "status_display",
                  "created_at", "resolved_at")
        read_only_fields = ("requested_by", "status", "created_at", "resolved_at")
