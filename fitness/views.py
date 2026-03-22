from django.db.models import Q
from django.db import transaction
from django.utils import timezone

from rest_framework.decorators import api_view, permission_classes, action, authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, NotFound
from rest_framework.viewsets import ModelViewSet
from datetime import timedelta


from .auth_jwt import create_access_token, create_refresh_token, decode_token, UsersJWTAuthentication
from .permissions import IsJWTAuthenticated

from django.db.models import Sum, F, Max, Count
from django.db.models.functions import TruncDate

from .models import (
    Exercises, WorkoutPlan, UserWeightHistory,
    SessionExercisesSets, WorkoutSession,
    SessionExercise, Goals, Categories, PlanExercise
)

from .serializers import (
    RegisterSerializer, ProfileUpdateSerializer,
    ExerciseSerializer, WorkoutPlanSerializer,
    LoginSerializer, UserSerializer,
    WorkoutSessionSerializer
)



@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "User created"}, status=201)
    return Response(serializer.errors, status=400)


@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    serializer = LoginSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)

    user = serializer.validated_data["user"]

    return Response({
        "access": create_access_token(user.id),
        "refresh": create_refresh_token(user.id)
    })


@api_view(["POST"])
@permission_classes([AllowAny])
def refresh_token(request):
    refresh = request.data.get("refresh")
    if not refresh:
        return Response({"error": "refresh token required"}, status=400)

    try:
        payload = decode_token(refresh)
    except Exception:
        return Response({"error": "invalid token"}, status=401)

    if payload.get("type") != "refresh":
        return Response({"error": "invalid token"}, status=401)

    return Response({
        "access": create_access_token(payload["user_id"])
    })



@api_view(["GET"])
@authentication_classes([UsersJWTAuthentication])
@permission_classes([IsJWTAuthenticated])
def get_profile(request):
    return Response(UserSerializer(request.user).data)


@api_view(["PATCH"])
@permission_classes([IsJWTAuthenticated])
def update_profile(request):
    serializer = ProfileUpdateSerializer(
        instance=request.user,
        data=request.data,
        partial=True
    )

    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Profile updated"})

    return Response(serializer.errors, status=400)




class ExerciseViewSet(ModelViewSet):
    serializer_class = ExerciseSerializer
    permission_classes = [IsJWTAuthenticated]


    def get_queryset(self):
        queryset = (
            Exercises.objects
            .filter(Q(User_id__isnull=True) | Q(User_id=self.request.user))
            .select_related("category_id")
            .prefetch_related("goals")
            .order_by("name")
        )

        category_id = self.request.GET.get("category_id")
        goal_id = self.request.GET.get("goal_id")

        if category_id:
            queryset = queryset.filter(category_id=category_id)

        if goal_id:
            queryset = queryset.filter(
                exercisesgoals__Goals_goal_id=goal_id
            )

        return queryset

    def perform_create(self, serializer):
        serializer.save(User_id=self.request.user)




class WorkoutPlanViewSet(ModelViewSet):
    serializer_class = WorkoutPlanSerializer
    permission_classes = [IsJWTAuthenticated]

    def get_queryset(self):
        return (
            WorkoutPlan.objects
            .filter(Q(User_id=self.request.user) | Q(User_id__isnull=True))
            .annotate(exercises_count=Count("planexercise"))
            .prefetch_related("planexercise_set__exercise_id")
        )

    def perform_create(self, serializer):
        serializer.save(User_id=self.request.user)

    def check_owner(self, plan):
        if plan.User_id and plan.User_id != self.request.user:
            raise PermissionDenied()

    @action(detail=True, methods=["POST"])
    def add_exercise(self, request, pk=None):
        plan = self.get_object()
        self.check_owner(plan)

        exercise_id = request.data.get("exercise_id")
        if not exercise_id:
            return Response({"error": "exercise_id required"}, status=400)

        exercise = Exercises.objects.filter(exercise_id=exercise_id).first()
        if not exercise:
            raise NotFound("Exercise not found")

        if exercise.User_id and exercise.User_id != request.user:
            raise PermissionDenied()

        order = PlanExercise.objects.filter(plan_id=plan).count() + 1

        pe = PlanExercise.objects.create(
            plan_id=plan,
            exercise_id=exercise,
            sets=request.data.get("sets", 3),
            reps=request.data.get("reps", 10),
            target_weight=request.data.get("target_weight", 0),
            order=order,
            day_of_week=request.data.get("day_of_week")
        )

    @action(detail=True, methods=["POST"])
    def clone(self, request, pk=None):
        plan = self.get_object()

        new_plan = WorkoutPlan.objects.create(
            name=plan.name + " (copy)",
            description=plan.description,
            User_id=request.user,
            goal=plan.goal
        )

        exercises = PlanExercise.objects.filter(plan_id=plan)

        for ex in exercises:
            PlanExercise.objects.create(
                plan_id=new_plan,
                exercise_id=ex.exercise_id,
                day_of_week=ex.day_of_week,
                sets=ex.sets,
                reps=ex.reps,
                target_weight=ex.target_weight,
                order=ex.order
            )

        return Response({
            "message": "Plan cloned",
            "plan_id": new_plan.plan_id
        })


        return Response({"plan_exercise_id": pe.id})


@api_view(["GET"])
@permission_classes([IsJWTAuthenticated])
def workout_history(request):

    sessions = (
        WorkoutSession.objects
        .filter(User_id=request.user, finished=True)
        .select_related("plan")
        .prefetch_related(
            "sessionexercise_set__sessionexercisessets_set",
            "sessionexercise_set__exercise_id"
        )
        .order_by("-date")
    )

    result = []

    for session in sessions:
        total_volume = 0
        exercises_data = []

        for ex in session.sessionexercise_set.all():
            sets = ex.sessionexercisessets_set.all()

            ex_volume = 0
            sets_done = 0

            sets_data = []

            for s in sets:
                if s.is_completed:
                    volume = (s.weight or 0) * (s.reps or 0)
                    ex_volume += volume
                    sets_done += 1

                sets_data.append({
                    "set_number": s.set_number,
                    "reps": s.reps,
                    "weight": s.weight,
                    "is_completed": s.is_completed,
                })

            total_volume += ex_volume

            exercises_data.append({
                "name": ex.exercise_id.name,
                "volume": ex_volume,
                "sets_done": sets_done,
                "total_sets": sets.count(),
                "sets": sets_data
            })

        result.append({
            "session_id": session.session_id,
            "plan_name": session.plan.name if session.plan else "Custom Workout",
            "date": session.date.isoformat(),
            "weekday": session.date.strftime("%A"),
            "weekday_short": session.date.strftime("%a"),
            "duration": session.duration_min or 0,
            "total_volume": total_volume,
            "exercises": exercises_data,
        })

    return Response(result)


@api_view(["POST"])
@permission_classes([IsJWTAuthenticated])
def start_workout_from_plan(request, plan_id):

    plan = WorkoutPlan.objects.filter(plan_id=plan_id).first()
    if not plan:
        raise NotFound()

    if plan.User_id and plan.User_id != request.user:
        raise PermissionDenied()

    with transaction.atomic():

        session = WorkoutSession.objects.create(
            User_id=request.user,
            date=timezone.now(),
            duration_min=0,
            finished=False
        )

        exercises = PlanExercise.objects.filter(plan_id=plan)

        for pe in exercises:
            se = SessionExercise.objects.create(
                session_id=session,
                exercise_id=pe.exercise_id
            )

            SessionExercisesSets.objects.bulk_create([
                SessionExercisesSets(
                    session_exercise_id=se,
                    set_number=i + 1,
                    reps=pe.reps,
                    weight=pe.target_weight
                )
                for i in range(pe.sets)
            ])

    return Response({"session_id": session.session_id})


@api_view(["PATCH"])
@permission_classes([IsJWTAuthenticated])
def complete_set(request, set_id):

    s = SessionExercisesSets.objects.select_related(
        "session_exercise_id__session_id"
    ).filter(set_id=set_id).first()

    if not s:
        raise NotFound()

    if s.session_exercise_id.session_id.User_id != request.user:
        raise PermissionDenied()

    s.is_completed = True
    s.save(update_fields=["is_completed"])

    se = s.session_exercise_id

    total = SessionExercisesSets.objects.filter(session_exercise_id=se).count()
    done = SessionExercisesSets.objects.filter(
        session_exercise_id=se,
        is_completed=True
    ).count()

    if total == done:
        se.is_completed = True
        se.save(update_fields=["is_completed"])

    return Response({"message": "Set completed"})


@api_view(["PATCH"])
@permission_classes([IsJWTAuthenticated])
def uncomplete_set(request, set_id):

    s = SessionExercisesSets.objects.select_related(
        "session_exercise_id__session_id"
    ).filter(set_id=set_id).first()

    if not s:
        raise NotFound()

    if s.session_exercise_id.session_id.User_id != request.user:
        raise PermissionDenied()

    s.is_completed = False
    s.save(update_fields=["is_completed"])

    se = s.session_exercise_id
    se.is_completed = False
    se.save(update_fields=["is_completed"])

    return Response({"message": "Set unchecked"})


@api_view(["PATCH"])
@permission_classes([IsJWTAuthenticated])
def finish_workout_session(request, session_id):

    session = WorkoutSession.objects.filter(session_id=session_id).first()
    if not session:
        raise NotFound()

    if session.User_id != request.user:
        raise PermissionDenied()

    if session.finished:
        return Response({"message": "Already finished"}, status=400)

    session.finished = True
    session.finished_at = timezone.now()

    if session.started_at:
        duration = (session.finished_at - session.started_at).total_seconds() // 60
        session.duration_min = int(duration)

    session.save(update_fields=["finished", "finished_at", "duration_min"])

    return Response({"message": "Workout finished"})


@api_view(["GET"])
@permission_classes([IsJWTAuthenticated])
def get_workout_session(request, session_id):

    session = WorkoutSession.objects.filter(
        session_id=session_id
    ).first()

    if not session:
        raise NotFound()

    if session.User_id != request.user:
        raise PermissionDenied()

    data = WorkoutSessionSerializer(session).data

    return Response(data)

@api_view(["PATCH"])
@permission_classes([IsJWTAuthenticated])
def update_set(request, set_id):

    s = SessionExercisesSets.objects.select_related(
        "session_exercise_id__session_id"
    ).filter(set_id=set_id).first()

    if not s:
        raise NotFound()

    if s.session_exercise_id.session_id.User_id != request.user:
        raise PermissionDenied()

    reps = request.data.get("reps")
    weight = request.data.get("weight")

    if reps is not None:
        s.reps = reps

    if weight is not None:
        s.weight = weight

    s.save()

    return Response({"message": "Set updated"})

@api_view(["GET"])
@permission_classes([IsJWTAuthenticated])
def get_active_session(request):

    session = WorkoutSession.objects.filter(
        User_id=request.user,
        finished=False
    ).order_by("-date").first()

    if not session:
        return Response({"session": None})

    return Response({
        "session_id": session.session_id
    })

@api_view(["GET"])
@permission_classes([IsJWTAuthenticated])
def workout_stats(request):
    total = WorkoutSession.objects.filter(
        User_id=request.user,
        finished=True
    ).count()

    return Response({"total_workouts": total})


@api_view(["GET"])
@permission_classes([IsJWTAuthenticated])
def weight_progress(request):
    weights = UserWeightHistory.objects.filter(
        Users_id=request.user
    ).order_by("measured_at")

    return Response([
        {"date": w.measured_at, "weight": w.weight}
        for w in weights
    ])




@api_view(["GET"])
def goals_list(request):
    return Response([
        {"id": g.goal_id, "name": g.name}
        for g in Goals.objects.all()
    ])


@api_view(["GET"])
def categories_list(request):
    return Response([
        {"id": c.category_id, "name": c.name}
        for c in Categories.objects.all()
    ])







@api_view(["GET"])
@permission_classes([IsJWTAuthenticated])
def exercise_progress(request, exercise_id):
    user = request.user

    data = SessionExercisesSets.objects.filter(
        session_exercise_id__exercise_id=exercise_id,
        session_exercise_id__session_id__User_id=user,
        is_completed=True
    ).annotate(
        day=TruncDate("session_exercise_id__session_id__date")
    ).values("day").annotate(
        weight=Max("weight")
    ).order_by("day")

    return Response([
        {
            "date": d["day"],
            "weight": d["weight"]
        }
        for d in data if d["day"]
    ])


@api_view(["GET"])
@permission_classes([IsJWTAuthenticated])
def one_rep_max(request, exercise_id):
    user = request.user

    sets = SessionExercisesSets.objects.filter(
        session_exercise_id__exercise_id=exercise_id,
        session_exercise_id__session_id__User_id=user,
        is_completed=True
    )

    best_1rm = 0

    for s in sets:
        if s.weight and s.reps:
            est = float(s.weight) * (1 + s.reps / 30)
            if est > best_1rm:
                best_1rm = est

    return Response({
        "exercise_id": exercise_id,
        "estimated_1rm": round(best_1rm, 2)
    })


@api_view(["GET"])
@permission_classes([IsJWTAuthenticated])
def analytics(request):
    user = request.user
    period = request.GET.get("period", "7d")

    now = timezone.now()

    if period == "7d":
        start = now - timedelta(days=7)
    elif period == "30d":
        start = now - timedelta(days=30)
    else:
        start = now - timedelta(days=180)

    sessions = WorkoutSession.objects.filter(
        User_id=user,
        finished=True,
        date__gte=start
    )

    sets = SessionExercisesSets.objects.filter(
        session_exercise_id__session_id__User_id=user,
        session_exercise_id__session_id__finished=True,
        session_exercise_id__session_id__date__gte=start,
        is_completed=True
    )

    total_workouts = sessions.count()

    total_duration = sessions.aggregate(
        total=Sum("duration_min")
    )["total"] or 0

    total_volume = sets.aggregate(
        total=Sum(F("weight") * F("reps"))
    )["total"] or 0

    volume_data = sets.annotate(
        day=TruncDate("session_exercise_id__session_id__date")
    ).values("day").annotate(
        value=Sum(F("weight") * F("reps"))
    ).order_by("day")

    duration_data = sessions.annotate(
        day=TruncDate("date")
    ).values("day").annotate(
        value=Sum("duration_min")
    ).order_by("day")

    frequency_data = sessions.annotate(
        day=TruncDate("date")
    ).values("day").annotate(
        value=Count("session_id")
    ).order_by("day")

    exercise_data = sets.values(
        "session_exercise_id__exercise_id__name"
    ).annotate(
        value=Sum(F("weight") * F("reps"))
    ).order_by("-value")[:5]

    prs = sets.values(
        "session_exercise_id__exercise_id__name"
    ).annotate(
        value=Max("weight")
    ).order_by("-value")[:5]

    muscles_raw = sets.values(
        "session_exercise_id__exercise_id__category_id__name"
    ).annotate(
        value=Sum(F("weight") * F("reps"))
    )

    total_muscle = sum([m["value"] for m in muscles_raw]) or 1

    muscles = [
        {
            "label": m["session_exercise_id__exercise_id__category_id__name"],
            "value": round((m["value"] / total_muscle) * 100, 1)
        }
        for m in muscles_raw
    ]

    return Response({
        "stats": {
            "total_workouts": total_workouts,
            "total_duration": total_duration,
            "total_volume": total_volume
        },

        "volume": [
            {"label": d["day"].strftime("%d %b"), "value": d["value"] or 0}
            for d in volume_data if d["day"]
        ],

        "duration": [
            {"label": d["day"].strftime("%d %b"), "value": d["value"] or 0}
            for d in duration_data if d["day"]
        ],

        "frequency": [
            {"label": d["day"].strftime("%a"), "value": d["value"]}
            for d in frequency_data if d["day"]
        ],

        "exercise_volume": [
            {"label": d["session_exercise_id__exercise_id__name"], "value": d["value"]}
            for d in exercise_data
        ],

        "prs": [
            {"exercise": d["session_exercise_id__exercise_id__name"], "max_weight": d["value"]}
            for d in prs
        ],

        "muscles": muscles
    })

