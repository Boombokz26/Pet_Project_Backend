from .models import (
    Users, Categories, Goals, Exercises, ExercisesGoals, WorkoutPlan, PlanExercise, WorkoutSession, WorkoutSession,
    SessionExercise, SessionExercisesSets,

)
from django.contrib import admin



admin.site.register(Users)
admin.site.register(Goals)

admin.site.register(ExercisesGoals)

@admin.register(Categories)
class CategoriesAdmin(admin.ModelAdmin):
    list_display = ("category_id", "name", "description")


class PlanExerciseInline(admin.TabularInline):
    model = PlanExercise
    extra = 5
    autocomplete_fields = ["exercise_id"]

@admin.register(WorkoutPlan)
class WorkoutPlanAdmin(admin.ModelAdmin):
    list_display = ("plan_id", "name", "created_at", "is_active")
    inlines = [PlanExerciseInline]


@admin.register(Exercises)
class ExercisesAdmin(admin.ModelAdmin):
    list_display = ("exercise_id", "name", "DifficultyLevel", "category_id")
    search_fields = ("name",)


@admin.register(PlanExercise)
class PlanExerciseAdmin(admin.ModelAdmin):
    list_display = ("plan_id", "exercise_id", "day_of_week", "sets", "reps", "order")

class SessionExercisesSetsInline(admin.TabularInline):
    model = SessionExercisesSets
    extra = 0

class SessionExerciseInline(admin.TabularInline):
    model = SessionExercise
    extra = 0

@admin.register(WorkoutSession)
class WorkoutSessionAdmin(admin.ModelAdmin):
    list_display = ("session_id", "User_id", "date", "duration_min", "finished")
    list_filter = ("finished", "date")
    inlines = [SessionExerciseInline]

@admin.register(SessionExercise)
class SessionExerciseAdmin(admin.ModelAdmin):
    list_display = ("session_exercise_id", "session_id", "exercise_id", "is_completed")
    inlines = [SessionExercisesSetsInline]

@admin.register(SessionExercisesSets)
class SessionExercisesSetsAdmin(admin.ModelAdmin):
    list_display = ("set_id", "session_exercise_id", "set_number", "reps", "weight", "is_completed")