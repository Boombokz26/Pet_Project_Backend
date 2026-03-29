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

    workout_stats,
    weight_progress,

    ExerciseViewSet,

    WorkoutPlanViewSet,
    workout_history, exercise_progress,
    one_rep_max, add_session_set, delete_session_set,

)

router = DefaultRouter()
router.register(r'exercises', ExerciseViewSet, basename='exercises')

router.register(r'plans', WorkoutPlanViewSet, basename='plans')

urlpatterns = [


    path("register/", register),
    path("login/", login),
    path("refresh/", refresh_token),


    path("profile/", get_profile),
    path("profile/update/", update_profile),


    path("sessions/start/<int:plan_id>/", start_workout_from_plan),
    path("sessions/<int:session_id>/", views.get_workout_session),
    path("sessions/active/", views.get_active_session),
    path("sessions/<int:session_id>/finish/", finish_workout_session),


    path("sets/<int:set_id>/complete/", complete_set),
    path("sets/<int:set_id>/uncomplete/", uncomplete_set),
    path("sets/<int:set_id>/update/", views.update_set),

    path("plan-sets/<int:set_id>/", views.plan_set_detail),
    path("plan-exercises/<int:plan_exercise_id>/add_set/", views.add_plan_set),

    path("session-sets/<int:session_exercise_id>/add/", add_session_set),
    path("session-sets/<int:set_id>/delete/", delete_session_set),


    path("stats/workouts/", workout_stats),
    path("stats/weight/", weight_progress),

    path("workouts/history/", workout_history),


    path("categories/", views.categories_list),
    path("goals/", views.goals_list),


    path("", include(router.urls)),



    path("stats/exercise/<int:exercise_id>/", exercise_progress),


    path("stats/1rm/<int:exercise_id>/", one_rep_max),
    path("analytics/", views.analytics)
]