from django.db import transaction
from django.utils import timezone

from .models import WorkoutPlan, WorkoutSession, PlanExercise, SessionExercise, SessionExerciseSets


@transaction.atomic
def create_session_from_plan(*, user, plan_id: int) -> WorkoutSession:
    plan = WorkoutPlan.objects.select_related("user").get(plan_id=plan_id)

    if plan.user_id != user.id:
        raise ValueError("Plan does not belong to user")

    session = WorkoutSession.objects.create(
        user=user,
        date=timezone.now(),
        duration_min=0,
        notes=None,
    )

    plan_exercises = PlanExercise.objects.filter(plan=plan).select_related("exercise").order_by("order", "id")

    for pe in plan_exercises:
        se = SessionExercise.objects.create(
            session=session,
            exercise=pe.exercise,
            notes=None,
        )

        n_sets = pe.sets or 1
        for i in range(1, n_sets + 1):
            SessionExerciseSets.objects.create(
                session_exercise=se,
                set_number=i,
                reps=pe.reps,
                weight=pe.target_weight,
            )

    return session
