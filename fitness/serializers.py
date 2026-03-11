from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import Users, Exercises, PlanExercise, WorkoutPlan, UserWeightHistory, WorkoutSession, \
    SessionExercise, SessionExercisesSets, Goals
from django.db import transaction
from django.contrib.auth.hashers import check_password
from django.utils import timezone

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    goal_id = serializers.IntegerField(write_only=True)
    weight_current = serializers.DecimalField(max_digits=5, decimal_places=2, write_only=True)
    class Meta:
        model = Users
        fields = ["email", "password", "name","height","goal_id","weight_current"]

    def validate_email(self, value):
        if Users.objects.filter(email=value).exists():
            raise serializers.ValidationError("User already exists")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        goal_id = validated_data.pop("goal_id")
        weight = validated_data.pop("weight_current")

        goal = Goals.objects.get(goal_id=goal_id)

        user = Users.objects.create(
            password_hash=make_password(password),
            signup_date=timezone.now().date(),
            goal=goal,
            **validated_data
        )

        UserWeightHistory.objects.create(
            Users_id=user,
            weight=weight,
            measured_at=timezone.now().date()
        )
        return user


class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = ["height"]

    def validate_height(self, value):
        if value <= 0:
            raise serializers.ValidationError("Height must be positive")
        return value


class ExerciseSerializer(serializers.ModelSerializer):

    category_name = serializers.CharField(source="category_id.name")

    goals = serializers.SerializerMethodField()

    class Meta:
        model = Exercises
        fields = [
            "exercise_id",
            "name",
            "description",
            "DifficultyLevel",
            "category_id",
            "category_name",
            "goals"
        ]

    def get_goals(self, obj):

        goals = obj.exercisesgoals_set.all()

        return [g.Goals_goal_id.name for g in goals]

class PlanExerciseSerializer(serializers.ModelSerializer):
    exercise_id = serializers.IntegerField()

    class Meta:
        model = PlanExercise
        fields = ["exercise_id", "day_of_week", "sets", "reps", "target_weight", "order"]


class WorkoutPlanSerializer(serializers.ModelSerializer):
    exercises = PlanExerciseSerializer(
        many=True,
        source="planexercise_set"   # ← ВАЖНО
    )

    class Meta:
        model = WorkoutPlan
        fields = ["plan_id", "name", "description", "exercises"]

    @transaction.atomic
    def create(self, validated_data):
        exercises_data = validated_data.pop("planexercise_set")

        workout_plan = WorkoutPlan.objects.create(
            User_id=self.context["request"].user,
            **validated_data
        )

        for exercise_item in exercises_data:
            exercise = Exercises.objects.get(
                exercise_id=exercise_item["exercise_id"],
                User_id=self.context["request"].user
            )

            PlanExercise.objects.create(
                plan_id=workout_plan,
                exercise_id=exercise,
                day_of_week=exercise_item["day_of_week"],
                sets=exercise_item["sets"],
                reps=exercise_item["reps"],
                target_weight=exercise_item["target_weight"],
                order=exercise_item["order"]
            )

        return workout_plan

class LoginSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        try:
            user = Users.objects.get(email=data["email"])
        except Users.DoesNotExist:
            raise serializers.ValidationError("Invalid credentials")

        if not check_password(data["password"], user.password_hash):
            raise serializers.ValidationError("Invalid credentials")

        return {"user": user}


class UserSerializer(serializers.ModelSerializer):
    weight = serializers.SerializerMethodField()
    goal = serializers.CharField(source="goal.name")
    class Meta:
        model = Users
        fields = ["id", "email", "name", "height", "goal","weight"]


    def get_weight(self, obj):
        last_weight = (
            UserWeightHistory.objects
            .filter(Users_id=obj)
            .order_by("-measured_at")
            .first()
        )

        return last_weight.weight if last_weight else None
class WeightHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserWeightHistory
        fields = ["id", "weight", "measured_at", "created_at"]

class WorkoutSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkoutSession
        fields = ["session_id", "date", "duration_min", "notes"]

class SessionExerciseSerializer(serializers.ModelSerializer):
    class Meta:
        model = SessionExercise
        fields = ["session_exercise_id", "session_id", "exercise_id", "notes"]

class SessionExerciseSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = SessionExercisesSets
        fields = ["set_id", "session_exercise_id", "set_number", "reps", "weight"]

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