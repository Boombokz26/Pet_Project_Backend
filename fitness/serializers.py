from rest_framework import serializers
from django.contrib.auth.hashers import make_password, check_password

from .models import (
    Users, Categories, Goals, Exercises, Equipment,
    WorkoutPlan, WorkoutSession, PlanExercise, SessionExercise,
    SessionExerciseSets
)


# ---------- AUTH ----------
class UserPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = ["id", "name", "email", "signup_date", "height", "weight"]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = Users
        fields = ["id", "name", "email", "password"]

    def validate_email(self, value):
        if Users.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value

    def create(self, validated_data):
        raw_password = validated_data.pop("password")
        validated_data["password_hash"] = make_password(raw_password)
        # signup_date можно не ставить — у тебя null=True
        return Users.objects.create(**validated_data)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs["email"]
        password = attrs["password"]

        user = Users.objects.filter(email=email).first()
        if not user:
            raise serializers.ValidationError("Invalid credentials")

        if not check_password(password, user.password_hash):
            raise serializers.ValidationError("Invalid credentials")

        attrs["user"] = user
        return attrs


# ---------- CATALOG ----------
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Categories
        fields = "__all__"


class GoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Goals
        fields = "__all__"


class EquipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipment
        fields = "__all__"


class ExerciseSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Exercises
        fields = "__all__"


# ---------- PLANS ----------
class PlanExerciseSerializer(serializers.ModelSerializer):
    exercise = ExerciseSerializer(read_only=True)

    class Meta:
        model = PlanExercise
        fields = ["id", "plan", "exercise", "day_of_week", "sets", "reps", "target_weight", "order"]


class WorkoutPlanSerializer(serializers.ModelSerializer):
    exercises = serializers.SerializerMethodField()

    class Meta:
        model = WorkoutPlan
        fields = ["plan_id", "user", "name", "created_at", "exercises"]
        read_only_fields = ["user", "created_at"]

    def get_exercises(self, obj):
        qs = PlanExercise.objects.filter(plan=obj).select_related("exercise", "exercise__category").order_by("order", "id")
        return PlanExerciseSerializer(qs, many=True).data


# ---------- SESSIONS ----------
class SessionExerciseSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = SessionExerciseSets
        fields = "__all__"


class SessionExerciseSerializer(serializers.ModelSerializer):
    sets = SessionExerciseSetSerializer(many=True, read_only=True)

    class Meta:
        model = SessionExercise
        fields = "__all__"


class WorkoutSessionSerializer(serializers.ModelSerializer):
    session_exercises = serializers.SerializerMethodField()

    class Meta:
        model = WorkoutSession
        fields = ["session_id", "user", "date", "duration_min", "notes", "session_exercises"]
        read_only_fields = ["user"]

    def get_session_exercises(self, obj):
        qs = SessionExercise.objects.filter(session=obj).select_related("exercise")
        return SessionExerciseSerializer(qs, many=True).data
