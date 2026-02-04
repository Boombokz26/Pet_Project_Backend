from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    register_view, login_view, refresh_view, me_view,
    CategoryViewSet, GoalViewSet, EquipmentViewSet, ExerciseViewSet,
    WorkoutPlanViewSet, WorkoutSessionViewSet, SessionExerciseViewSet, SessionExerciseSetViewSet
)

router = DefaultRouter()
router.register("categories", CategoryViewSet, basename="categories")
router.register("goals", GoalViewSet, basename="goals")
router.register("equipment", EquipmentViewSet, basename="equipment")
router.register("exercises", ExerciseViewSet, basename="exercises")

router.register("plans", WorkoutPlanViewSet, basename="plans")
router.register("sessions", WorkoutSessionViewSet, basename="sessions")
router.register("session-exercises", SessionExerciseViewSet, basename="session-exercises")
router.register("session-sets", SessionExerciseSetViewSet, basename="session-sets")

urlpatterns = [
    path("auth/register/", register_view),
    path("auth/login/", login_view),
    path("auth/refresh/", refresh_view),
    path("auth/me/", me_view),

    path("", include(router.urls)),
]
