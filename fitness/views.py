from django.db.models import Q, Count
from django.db import transaction
from django.utils import timezone

from rest_framework.decorators import api_view, permission_classes, action, authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, NotFound
from rest_framework.viewsets import ModelViewSet

from django_filters.rest_framework import DjangoFilterBackend

from .auth_jwt import create_access_token, create_refresh_token, decode_token, UsersJWTAuthentication
from .permissions import IsJWTAuthenticated

from .models import (
    Exercises, WorkoutPlan, UserWeightHistory,
    SessionExercisesSets, WorkoutSession,
    SessionExercise, Goals, Categories, PlanExercise
)

from .serializers import (
    RegisterSerializer, ProfileUpdateSerializer,
    ExerciseSerializer, WorkoutPlanSerializer,
    LoginSerializer, UserSerializer,
    WeightHistorySerializer,
    WorkoutSaveSerializer
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

        return Response({"plan_exercise_id": pe.id})




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
    session.save(update_fields=["finished"])

    return Response({"message": "Workout finished"})




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