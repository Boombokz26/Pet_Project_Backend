from rest_framework import viewsets
from .models import Users, WorkoutSession, SessionExercise, SessionExerciseSets
from .serializers import (
    UsersSerializer, WorkoutSessionSerializer,
    SessionExerciseSerializer, SessionExerciseSetsSerializer
)


class UsersViewSet(viewsets.ModelViewSet):
    queryset = Users.objects.all()
    serializer_class = UsersSerializer


class WorkoutSessionViewSet(viewsets.ModelViewSet):
    queryset = WorkoutSession.objects.all()
    serializer_class = WorkoutSessionSerializer


class SessionExerciseViewSet(viewsets.ModelViewSet):
    queryset = SessionExercise.objects.all()
    serializer_class = SessionExerciseSerializer


class SessionExerciseSetsViewSet(viewsets.ModelViewSet):
    queryset = SessionExerciseSets.objects.all()
    serializer_class = SessionExerciseSetsSerializer
