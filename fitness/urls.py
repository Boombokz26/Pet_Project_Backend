from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views
from .views import (
    register,
    login,
    refresh_token,

    get_profile,
    update_profile,

    start_workout_from_plan,
    finish_workout_session,
    complete_set,
    uncomplete_set,

    # exercise_progress,
    workout_stats,
    weight_progress,

    ExerciseViewSet,
    # WeightHistoryViewSet,
    WorkoutPlanViewSet,
    # save_workout
)

router = DefaultRouter()
router.register(r'exercises', ExerciseViewSet, basename='exercises')
# router.register(r'weight-history', WeightHistoryViewSet, basename='weight-history')
router.register(r'plans', WorkoutPlanViewSet, basename='plans')

urlpatterns = [

    # AUTH
    path("register/", register),
    path("login/", login),
    path("token/refresh/", refresh_token),

    # PROFILE
    path("profile/", get_profile),
    path("profile/update/", update_profile),

    # 🔥 WORKOUT FLOW (НОВЫЙ)
    path("workout/start/<int:plan_id>/", start_workout_from_plan),
    path("workout/finish/<int:session_id>/", finish_workout_session),

    # CHECKLIST
    path("workout/set/complete/<int:set_id>/", complete_set),
    path("workout/set/uncomplete/<int:set_id>/", uncomplete_set),

    # path("exercise-progress/<int:exercise_id>/", exercise_progress),
    path("workout-stats/", workout_stats),
    path("weight-progress/", weight_progress),

    # path("workout/save/", save_workout),

    # STATIC
    path("categories/", views.categories_list),
    path("goals/", views.goals_list),

    # ROUTER
    path("", include(router.urls)),
]