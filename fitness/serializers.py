from rest_framework import serializers
from .models import Users, WorkoutSession, SessionExercise, SessionExerciseSets


class UsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = "__all__"


class WorkoutSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkoutSession
        fields = "__all__"


class SessionExerciseSerializer(serializers.ModelSerializer):
    class Meta:
        model = SessionExercise
        fields = "__all__"


class SessionExerciseSetsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SessionExerciseSets
        fields = "__all__"
