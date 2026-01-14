from django.db import models


class Users(models.Model):
    id = models.AutoField(primary_key=True)
    email = models.CharField(max_length=45, unique=True)
    password_hash = models.CharField(max_length=255)
    name = models.CharField(max_length=45)
    signup_date = models.DateTimeField(null=True, blank=True)
    height = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    weight = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = "users"


class Categories(models.Model):
    category_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=45)
    description = models.CharField(max_length=45)

    class Meta:
        db_table = "categories"


class Goals(models.Model):
    goal_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(Users, on_delete=models.CASCADE, db_column="user_id", related_name="goals")
    goal_type = models.CharField(max_length=45)
    target_value = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    class Meta:
        db_table = "goals"


class Exercises(models.Model):
    exercise_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=45)
    category = models.ForeignKey(Categories, on_delete=models.SET_NULL, null=True, db_column="category_id")
    description = models.CharField(max_length=45)

    class Meta:
        db_table = "exercises"


class Equipment(models.Model):
    equipment_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=45)
    description = models.CharField(max_length=45)

    class Meta:
        db_table = "equipment"


class WorkoutPlan(models.Model):
    plan_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(Users, on_delete=models.CASCADE, db_column="user_id", related_name="plans")
    name = models.CharField(max_length=45)
    created_at = models.DateTimeField()

    class Meta:
        db_table = "workoutplan"


class WorkoutSession(models.Model):
    session_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(Users, on_delete=models.CASCADE, db_column="user_id", related_name="sessions")
    date = models.DateTimeField()
    duration_min = models.IntegerField()
    notes = models.CharField(max_length=45, null=True, blank=True)

    class Meta:
        db_table = "workoutsession"


# ⚠️ В SQL тут составной PK (plan_id, exercise_id).
# В Django делаем обычную таблицу с id + unique_together
class PlanExercise(models.Model):
    id = models.AutoField(primary_key=True)
    plan = models.ForeignKey(WorkoutPlan, on_delete=models.CASCADE, db_column="plan_id")
    exercise = models.ForeignKey(Exercises, on_delete=models.CASCADE, db_column="exercise_id")
    day_of_week = models.CharField(max_length=45, null=True, blank=True)
    sets = models.IntegerField(null=True, blank=True)
    reps = models.IntegerField(null=True, blank=True)
    target_weight = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    order = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "planexercise"
        unique_together = ("plan", "exercise")


class SessionExercise(models.Model):
    session_exercise_id = models.AutoField(primary_key=True)
    session = models.ForeignKey(WorkoutSession, on_delete=models.CASCADE, db_column="session_id", related_name="session_exercises")
    exercise = models.ForeignKey(Exercises, on_delete=models.CASCADE, db_column="exercise_id")
    notes = models.CharField(max_length=45, null=True, blank=True)

    class Meta:
        db_table = "sessionexercise"


# ⚠️ В SQL тут составной PK (exercise_id, equipment_id).
# В Django делаем id + unique_together
class ExerciseEquipment(models.Model):
    id = models.AutoField(primary_key=True)
    exercise = models.ForeignKey(Exercises, on_delete=models.CASCADE, db_column="exercise_id")
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, db_column="equipment_id")

    class Meta:
        db_table = "exerciseequipment"
        unique_together = ("exercise", "equipment")


class SessionExerciseSets(models.Model):
    set_id = models.AutoField(primary_key=True)
    session_exercise = models.ForeignKey(SessionExercise, on_delete=models.CASCADE, db_column="session_exercise_id", related_name="sets")
    set_number = models.IntegerField(null=True, blank=True)
    reps = models.IntegerField(null=True, blank=True)
    weight = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = "sessionexercisesets"
