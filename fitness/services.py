from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum, F, FloatField
from django.db.models.functions import Cast, TruncDate

from .models import WorkoutPlan, PlanExercise, WorkoutSession, SessionExercise, SessionExerciseSet


def get_active_plan(user):
    return WorkoutPlan.objects.filter(user=user, is_active=True).first()


def start_workout(user):
    plan = get_active_plan(user)
    session = WorkoutSession.objects.create(user=user, plan=plan, date=timezone.now())

    if plan:
        weekday = timezone.localdate().weekday()
        plan_exs = PlanExercise.objects.filter(plan=plan, day_of_week=weekday).select_related("exercise").order_by("order", "id")
        SessionExercise.objects.bulk_create([
            SessionExercise(session=session, exercise=pe.exercise, order=pe.order)
            for pe in plan_exs
        ])

    return session


def dashboard(user):
    today = timezone.localdate()
    start_date = today - timedelta(days=6)

    plan = get_active_plan(user)
    weekday = today.weekday()

    todays_workout = None
    if plan and PlanExercise.objects.filter(plan=plan, day_of_week=weekday).exists():
        todays_workout = {"plan_id": plan.id, "subtitle": plan.name}

    qs = (
        SessionExerciseSet.objects
        .filter(session_exercise__session__user=user,
                session_exercise__session__date__date__gte=start_date,
                session_exercise__session__date__date__lte=today)
        .annotate(d=TruncDate("session_exercise__session__date"))
        .annotate(v=Cast(F("weight"), FloatField()) * Cast(F("reps"), FloatField()))
        .values("d")
        .annotate(total=Sum("v"))
    )

    by_date = {row["d"].isoformat(): float(row["total"] or 0.0) for row in qs}

    last_7 = []
    for i in range(7):
        d = (start_date + timedelta(days=i)).isoformat()
        last_7.append({"date": d, "volume_kg": round(by_date.get(d, 0.0), 2)})

    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    workouts_this_week = WorkoutSession.objects.filter(
        user=user, date__date__gte=week_start, date__date__lte=week_end
    ).count()

    total_lifted_this_week = round(sum(x["volume_kg"] for x in last_7), 2)

    name = getattr(getattr(user, "profile", None), "name", "") or user.username

    return {
        "greeting_name": name,
        "todays_workout": ({"title": "Today's Workout", **todays_workout} if todays_workout else None),
        "stats": {
            "last_7_days_volume": last_7,
            "workouts_this_week": workouts_this_week,
            "total_lifted_this_week_kg": total_lifted_this_week,
        },
    }
