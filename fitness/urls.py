from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views
from .views import (
    register,
    login,
    get_profile,
    update_profile,

    start_workout_session,
    finish_workout_session,
    add_exercise_to_session,
    add_set_to_exercise,

    exercise_progress,
    workout_stats,
    weight_progress,

    ExerciseViewSet,
    WorkoutPlanViewSet,
    WeightHistoryViewSet, save_workout, refresh_token
)

router = DefaultRouter()

router.register(r'exercises', ExerciseViewSet, basename='exercises')
router.register(r'workout-plans', WorkoutPlanViewSet, basename='workout-plans')
router.register(r'weight-history', WeightHistoryViewSet, basename='weight-history')


urlpatterns = [

    # AUTH
    path("register/", register),
    path("login/", login),

    path("token/refresh/", refresh_token),

    # PROFILE
    path("profile/", get_profile),
    path("profile/update/", update_profile),

    # WORKOUT SESSION
    path("workout/start/", start_workout_session),
    path("workout/finish/<int:session_id>/", finish_workout_session),
    path("workout/add-exercise/", add_exercise_to_session),
    path("workout/add-set/", add_set_to_exercise),

    # ANALYTICS
    path("exercise-progress/<int:exercise_id>/", exercise_progress),
    path("workout-stats/", workout_stats),
    path("weight-progress/", weight_progress),

    # ROUTER
    path("", include(router.urls)),
    path("workout/save/", save_workout),

    # GOALS
    path("categories/", views.categories_list),
    path("goals/", views.goals_list)
]