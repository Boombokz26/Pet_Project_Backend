from django.contrib import admin
from .models import (
    Users, Categories, Goals, Exercises, ExercisesGoals, WorkoutPlan, PlanExercise
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