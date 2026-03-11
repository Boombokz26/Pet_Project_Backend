from django.db import models

class Users(models.Model):
    id = models.AutoField(primary_key=True)
    email = models.CharField(max_length=255,unique=True)
    password_hash = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    signup_date = models.DateField()
    height = models.DecimalField(max_digits=10, decimal_places=2)
    goal = models.ForeignKey(
        "Goals",
        on_delete=models.SET_NULL,
        null=True,
        db_column="goal_id"
    )

    def __str__(self):
        return f"{self.id} - {self.name} ({self.email})"

    class Meta:
        db_table = "Users"

class UserWeightHistory(models.Model):
    id = models.AutoField(primary_key=True)
    Users_id = models.ForeignKey(
        Users,
        on_delete=models.CASCADE,
        db_column="Users_id"
    )
    weight = models.DecimalField(max_digits=5, decimal_places=2)
    measured_at = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "UserWeightHistory"

class WorkoutPlan(models.Model):
    plan_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    created_at = models.DateField()
    is_active = models.BooleanField(default=True)  # TINYINT
    User_id = models.ForeignKey(
        Users,
        on_delete=models.CASCADE,
        db_column="User_id"
    )

    class Meta:
        db_table = "WorkoutPlan"


class Exercises(models.Model):
    exercise_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    image_url = models.CharField(max_length=255)
    goals = models.ManyToManyField(
        "Goals",
        through="ExercisesGoals",
        related_name="exercises"
    )
    User_id = models.ForeignKey(
        Users,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column="User_id"
    )
    category_id = models.ForeignKey(
        "Categories",
        on_delete=models.CASCADE,
        db_column="category_id"
    )
    DifficultyLevel = models.CharField(max_length=30)

    def __str__(self):
        return f"{self.exercise_id}- {self.User_id} - {self.name}"

    class Meta:
        db_table = "Exercises"

class Categories(models.Model):
    category_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.category_id} - {self.name}"

    class Meta:
        db_table = "Categories"

class Goals(models.Model):
    goal_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.goal_id} - {self.name}"

    class Meta:
        db_table = "Goals"

class ExercisesGoals(models.Model):
    Exercises_exercise_id = models.ForeignKey(
        Exercises,
        on_delete=models.CASCADE,
        db_column="Exercises_exercise_id"
    )
    Goals_goal_id = models.ForeignKey(
        Goals,
        on_delete=models.CASCADE,
        db_column="Goals_goal_id"
    )

    class Meta:
        db_table = "ExercisesGoals"
        unique_together = ("Exercises_exercise_id", "Goals_goal_id")

class Equipment(models.Model):
    equipment_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255)

    class Meta:
        db_table = "Equipment"

class ExerciseEquipment(models.Model):
    exercise_id = models.ForeignKey(
        Exercises,
        on_delete=models.CASCADE,
        db_column="exercise_id"
    )
    equipment_id = models.ForeignKey(
        Equipment,
        on_delete=models.CASCADE,
        db_column="equipment_id"
    )

    class Meta:
        db_table = "ExerciseEquipment"
        unique_together = ("exercise_id", "equipment_id")

class PlanExercise(models.Model):
    plan_id = models.ForeignKey(
        WorkoutPlan,
        on_delete=models.CASCADE,
        db_column="plan_id"
    )
    exercise_id = models.ForeignKey(
        Exercises,
        on_delete=models.CASCADE,
        db_column="exercise_id"
    )
    day_of_week = models.CharField(max_length=30)
    sets = models.IntegerField()
    reps = models.IntegerField()
    target_weight = models.DecimalField(max_digits=10, decimal_places=2)
    order = models.IntegerField()

    class Meta:
        db_table = "PlanExercise"

class WorkoutSession(models.Model):
    session_id = models.AutoField(primary_key=True)
    date = models.DateTimeField()
    duration_min = models.IntegerField()
    notes = models.CharField(max_length=255, blank=True)
    User_id = models.ForeignKey(
        Users,
        on_delete=models.CASCADE,
        db_column="User_id"
    )

    class Meta:
        db_table = "WorkoutSession"

class SessionExercise(models.Model):
    session_id = models.ForeignKey(
        WorkoutSession,
        on_delete=models.CASCADE,
        db_column="session_id"
    )
    exercise_id = models.ForeignKey(
        Exercises,
        on_delete=models.CASCADE,
        db_column="exercise_id"
    )
    notes = models.CharField(max_length=255)
    session_exercise_id = models.AutoField(primary_key=True)

    class Meta:
        db_table = "SessionExercise"



class SessionExercisesSets(models.Model):
    set_id = models.AutoField(primary_key=True)
    session_exercise_id = models.ForeignKey(
        SessionExercise,
        on_delete=models.CASCADE,
        db_column="session_exercise_id"
    )
    set_number = models.IntegerField()
    reps = models.IntegerField()
    weight = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = "SessionExercisesSets"