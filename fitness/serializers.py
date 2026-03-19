from rest_framework import serializers
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
from django.db import transaction

from .models import (
    Users, Exercises, PlanExercise, WorkoutPlan,
    UserWeightHistory, WorkoutSession,
    SessionExercise, SessionExercisesSets, Goals
)



class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    goal_id = serializers.IntegerField(write_only=True)
    weight_current = serializers.DecimalField(max_digits=5, decimal_places=2, write_only=True)

    class Meta:
        model = Users
        fields = ["email", "password", "name", "height", "goal_id", "weight_current"]

    def validate_email(self, value):
        if Users.objects.filter(email=value).exists():
            raise serializers.ValidationError("User already exists")
        return value

    def create(self, validated_data):
        with transaction.atomic():
            password = validated_data.pop("password")
            goal_id = validated_data.pop("goal_id")
            weight = validated_data.pop("weight_current")

            user = Users.objects.create(
                password_hash=make_password(password),
                signup_date=timezone.now().date(),
                goal_id=goal_id,
                **validated_data
            )

            UserWeightHistory.objects.create(
                Users_id=user,
                weight=weight,
                measured_at=timezone.now().date()
            )

        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        user = Users.objects.filter(email=data["email"]).first()

        if not user or not check_password(data["password"], user.password_hash):
            raise serializers.ValidationError("Invalid credentials")

        return {"user": user}




class UserSerializer(serializers.ModelSerializer):
    weight = serializers.SerializerMethodField()
    goal = serializers.CharField(source="goal.name")

    class Meta:
        model = Users
        fields = ["id", "email", "name", "height", "goal", "weight"]

    def get_weight(self, obj):
        last_weight = (
            UserWeightHistory.objects
            .filter(Users_id=obj)
            .order_by("-measured_at")
            .first()
        )
        return last_weight.weight if last_weight else None


class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = ["height"]

    def validate_height(self, value):
        if value <= 0:
            raise serializers.ValidationError("Height must be positive")
        return value




class ExerciseSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category_id.name", read_only=True)

    goals = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field="name"
    )

    class Meta:
        model = Exercises
        fields = [
            "exercise_id",
            "name",
            "description",
            "DifficultyLevel",
            "category_id",
            "category_name",
            "goals",
            "User_id"
        ]




class PlanExerciseSerializer(serializers.ModelSerializer):
    plan_exercise_id = serializers.IntegerField(source="id", read_only=True)
    exercise_name = serializers.CharField(source="exercise_id.name", read_only=True)

    class Meta:
        model = PlanExercise
        fields = [
            "plan_exercise_id",
            "exercise_id",
            "exercise_name",
            "sets",
            "reps",
            "target_weight",
            "order"
        ]


class WorkoutPlanSerializer(serializers.ModelSerializer):
    exercises_count = serializers.IntegerField(read_only=True)

    exercises = PlanExerciseSerializer(
        source="planexercise_set",
        many=True,
        read_only=True
    )

    goal_name = serializers.CharField(source="goal.name", read_only=True)

    class Meta:
        model = WorkoutPlan
        fields = "__all__"
        read_only_fields = ["User_id"]




class SessionExerciseSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = SessionExercisesSets
        fields = [
            "set_id",
            "set_number",
            "reps",
            "weight",
            "is_completed"
        ]


class SessionExerciseSerializer(serializers.ModelSerializer):
    exercise_name = serializers.CharField(source="exercise_id.name", read_only=True)

    sets = SessionExerciseSetSerializer(
        source="sessionexercisessets_set",
        many=True,
        read_only=True
    )

    class Meta:
        model = SessionExercise
        fields = [
            "session_exercise_id",
            "exercise_id",
            "exercise_name",
            "notes",
            "is_completed",
            "sets"
        ]


class WorkoutSessionSerializer(serializers.ModelSerializer):
    exercises = SessionExerciseSerializer(
        source="sessionexercise_set",
        many=True,
        read_only=True
    )

    class Meta:
        model = WorkoutSession
        fields = [
            "session_id",
            "date",
            "duration_min",
            "notes",
            "exercises"
        ]




class WeightHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserWeightHistory
        fields = ["id", "weight", "measured_at", "created_at"]




class WorkoutSetSerializer(serializers.Serializer):
    weight = serializers.DecimalField(max_digits=5, decimal_places=2)
    reps = serializers.IntegerField()


class WorkoutExerciseSerializer(serializers.Serializer):
    exercise_id = serializers.IntegerField()
    sets = WorkoutSetSerializer(many=True)


class WorkoutSaveSerializer(serializers.Serializer):
    date = serializers.DateField()
    duration_min = serializers.IntegerField()
    notes = serializers.CharField(required=False)
    exercises = WorkoutExerciseSerializer(many=True)