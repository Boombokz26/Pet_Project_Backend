from django.db.models import Q
from rest_framework.decorators import api_view, permission_classes, action, authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, NotFound
from rest_framework.viewsets import ModelViewSet
from .auth_jwt import create_access_token, create_refresh_token, decode_token, UsersJWTAuthentication
from .permissions import IsJWTAuthenticated
from django_filters.rest_framework import DjangoFilterBackend


from .models import (
    Exercises, WorkoutPlan, UserWeightHistory, SessionExercisesSets, WorkoutSession,
    SessionExercise, Goals, Categories
)
from .serializers import RegisterSerializer, ProfileUpdateSerializer, ExerciseSerializer, WorkoutPlanSerializer, \
    LoginSerializer, UserSerializer, WeightHistorySerializer, WorkoutSessionSerializer, SessionExerciseSerializer, \
    SessionExerciseSetSerializer, WorkoutSaveSerializer


@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()
        return Response({"message": "User created successfully"}, status=201)

    return Response(serializer.errors, status=400)

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
        return Response({"message": "Profile updated"}, status=200)

    return Response(serializer.errors, status=400)

class ExerciseViewSet(ModelViewSet):

    serializer_class = ExerciseSerializer
    permission_classes = [IsJWTAuthenticated]

    filter_backends = [DjangoFilterBackend]

    filterset_fields = {
        "category_id": ["exact"],
        "goals__goal_id": ["exact"],
    }

    def get_queryset(self):

        queryset = Exercises.objects.filter(
            Q(User_id__isnull=True) | Q(User_id=self.request.user)
        )

        category = self.request.query_params.get("category_id")
        goal = self.request.query_params.get("goal_id")

        if category:
            queryset = queryset.filter(category_id=category)

        if goal:
            queryset = queryset.filter(
                exercisesgoals__Goals_goal_id=goal
            )

        return queryset.select_related(
            "category_id"
        ).prefetch_related(
            "exercisesgoals_set__Goals_goal_id"
        ).order_by("name")

# class WorkoutPlanViewSet(ModelViewSet):
#     serializer_class = WorkoutPlanSerializer
#     permission_classes = [IsJWTAuthenticated]
#
#
#     def get_queryset(self):
#         return WorkoutPlan.objects.filter(User_id=self.request.user)
#
#
#     def perform_create(self, serializer):
#         serializer.save(User_id=self.request.user)
#
#
#     def perform_update(self, serializer):
#         if serializer.instance.User_id != self.request.user:
#             raise PermissionDenied("You cannot edit this plan")
#         serializer.save()
#
#
#     def perform_destroy(self, instance):
#         if instance.User_id != self.request.user:
#             raise PermissionDenied("You cannot delete this plan")
#
#         instance.is_active = 0
#         instance.save()
#
#
#     @action(detail=False, methods=["get"])
#     def active(self, request):
#         plans = self.get_queryset().filter(is_active=1)
#         serializer = self.get_serializer(plans, many=True)
#         return Response(serializer.data)
#
#
#     @action(detail=True, methods=["patch"])
#     def deactivate(self, request, pk=None):
#         plan = self.get_object()
#
#         if plan.User_id != request.user:
#             raise PermissionDenied("You cannot modify this plan")
#
#         plan.is_active = 0
#         plan.save()
#
#         return Response({"message": "Plan deactivated"})
#

@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    serializer = LoginSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=400)

    user = serializer.validated_data["user"]

    access = create_access_token(user.id)
    refresh = create_refresh_token(user.id)

    return Response({
        "access": access,
        "refresh": refresh
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
        return Response({"error": "refresh token required"}, status=401)

    user_id = payload.get("user_id")

    access = create_access_token(user_id)

    return Response({
        "access": access
    })


@api_view(["GET"])
@authentication_classes([UsersJWTAuthentication])
@permission_classes([IsJWTAuthenticated])
def get_profile(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data)



class WeightHistoryViewSet(ModelViewSet):
    serializer_class = WeightHistorySerializer
    permission_classes = [IsJWTAuthenticated]

    def get_queryset(self):
        return UserWeightHistory.objects.filter(Users_id=self.request.user)

    def perform_create(self, serializer):
        serializer.save(Users_id=self.request.user)


@api_view(["POST"])
@permission_classes([IsJWTAuthenticated])
def start_workout_session(request):
    serializer = WorkoutSessionSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save(User_id=request.user)
        return Response(serializer.data, status=201)

    return Response(serializer.errors, status=400)

@api_view(["PATCH"])
@permission_classes([IsJWTAuthenticated])
def finish_workout_session(request, session_id):

    try:
        session = WorkoutSession.objects.get(session_id=session_id)
    except WorkoutSession.DoesNotExist:
        raise NotFound("Session not found")

    if session.User_id != request.user:
        raise PermissionDenied()

    if session.finished:
        return Response({"message": "Session already finished"}, status=400)

    session.finished = True
    session.save()

    return Response({"message": "Workout finished"})

@api_view(["POST"])
@permission_classes([IsJWTAuthenticated])
def add_exercise_to_session(request):

    session_id = request.data.get("session_id")

    if not session_id:
        return Response({"error": "session_id required"}, status=400)

    try:
        session = WorkoutSession.objects.get(session_id=session_id)
    except WorkoutSession.DoesNotExist:
        raise NotFound("Session not found")

    if session.User_id != request.user:
        raise PermissionDenied("You cannot modify this session")

    exercise_id = request.data.get("exercise_id")

    try:
        exercise = Exercises.objects.get(exercise_id=exercise_id)
    except Exercises.DoesNotExist:
        raise NotFound("Exercise not found")

    if exercise.User_id != request.user:
        raise PermissionDenied("You cannot use this exercise")

    serializer = SessionExerciseSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save(session_id=session)
        return Response(serializer.data, status=201)

    return Response(serializer.errors, status=400)

@api_view(["POST"])
@permission_classes([IsJWTAuthenticated])
def add_set_to_exercise(request):

    session_exercise_id = request.data.get("session_exercise_id")

    if not session_exercise_id:
        return Response({"error": "session_exercise_id required"}, status=400)

    try:
        session_exercise = SessionExercise.objects.get(session_exercise_id=session_exercise_id)
    except SessionExercise.DoesNotExist:
        raise NotFound("Exercise not found")

    if session_exercise.session_id.User_id != request.user:
        raise PermissionDenied("You cannot modify this workout")

    serializer = SessionExerciseSetSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save(session_exercise_id=session_exercise)
        return Response(serializer.data, status=201)

    return Response(serializer.errors, status=400)


@api_view(["GET"])
@permission_classes([IsJWTAuthenticated])
def exercise_progress(request, exercise_id):
    try:
        exercise = Exercises.objects.get(exercise_id=exercise_id)
    except Exercises.DoesNotExist:
        raise NotFound("Exercise not found")

    if exercise.User_id != request.user:
        raise PermissionDenied("You cannot access this exercise")
    sets = SessionExercisesSets.objects.filter(
        session_exercise_id__exercise_id=exercise_id,
        session_exercise_id__session_id__User_id=request.user
    ).order_by("session_exercise_id__session_id__date")

    data = []
    for s in sets:
        data.append({
            "date": s.session_exercise_id.session_id.date,
            "weight": s.weight,
            "reps": s.reps
        })

    return Response(data)

@api_view(["GET"])
@permission_classes([IsJWTAuthenticated])
def workout_stats(request):


    sessions = WorkoutSession.objects.filter(
        User_id=request.user,
        finished=True
    )

    total_workouts = sessions.count()

    return Response({
        "total_workouts": total_workouts
    })

@api_view(["GET"])
@permission_classes([IsJWTAuthenticated])
def weight_progress(request):


    weights = UserWeightHistory.objects.filter(
        Users_id=request.user
    ).order_by("measured_at")

    data = []

    for w in weights:
        data.append({
            "date": w.measured_at,
            "weight": w.weight
        })

    return Response(data)

@api_view(["POST"])
@permission_classes([IsJWTAuthenticated])
def save_workout(request):

    serializer = WorkoutSaveSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=400)

    data = serializer.validated_data

    session = WorkoutSession.objects.create(
        User_id=request.user,
        date=data["date"],
        duration_min=data["duration_min"],
        notes=data.get("notes", "")
    )

    for ex in data["exercises"]:

        session_exercise = SessionExercise.objects.create(
            session_id=session,
            exercise_id_id=ex["exercise_id"]
        )

        for i, s in enumerate(ex["sets"], start=1):
            SessionExercisesSets.objects.create(
                session_exercise_id=session_exercise,
                set_number=i,
                weight=s["weight"],
                reps=s["reps"]
            )

    return Response({"message": "Workout saved"}, status=201)

@api_view(["GET"])
def goals_list(request):

    goals = Goals.objects.all()

    data = [
        {
            "id": g.goal_id,
            "name": g.name
        }
        for g in goals
    ]

    return Response(data)

@api_view(["GET"])
def categories_list(request):

    categories = Categories.objects.all()

    data = [
        {
            "id": c.category_id,
            "name": c.name
        }
        for c in categories
    ]

    return Response(data)