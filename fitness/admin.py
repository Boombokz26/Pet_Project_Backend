from django.contrib import admin
from .models import (
    Users, Categories, Goals, Exercises, Equipment,
    WorkoutPlan, WorkoutSession, PlanExercise,
    SessionExercise, ExerciseEquipment, SessionExerciseSets
)

admin.site.register(Users)
admin.site.register(Categories)
admin.site.register(Goals)
admin.site.register(Exercises)
admin.site.register(Equipment)
admin.site.register(WorkoutPlan)
admin.site.register(WorkoutSession)
admin.site.register(PlanExercise)
admin.site.register(SessionExercise)
admin.site.register(ExerciseEquipment)
admin.site.register(SessionExerciseSets)
