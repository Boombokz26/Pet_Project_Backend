from django.contrib import admin
from .models import (
    Users, Categories, Goals, Exercises, ExercisesGoals
)
from django.contrib import admin



admin.site.register(Users)
admin.site.register(Goals)
admin.site.register(Exercises)
admin.site.register(ExercisesGoals)

@admin.register(Categories)
class CategoriesAdmin(admin.ModelAdmin):
    list_display = ("category_id", "name", "description")
