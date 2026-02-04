from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, NotFound

from .auth_jwt import create_access_token, create_refresh_token, decode_token
from .services import create_session_from_plan

from .models import (
    Users, Categories, Goals, Exercises, Equipment,
    WorkoutPlan, WorkoutSession, SessionExercise, SessionExerciseSets
)
from .serializers import (
    UserPublicSerializer, RegisterSerializer, LoginSerializer,
    CategorySerializer, GoalSerializer, ExerciseSerializer, EquipmentSerializer,
    WorkoutPlanSerializer, WorkoutSessionSerializer, SessionExerciseSerializer, SessionExerciseSetSerializer
)


# ---------- AUTH ----------
@api_view(["POST"])
@permission_classes([AllowAny])
def register_view(request):
    s = RegisterSerializer(data=request.data)
    s.is_valid(raise_exception=True)
    user = s.save()
    return Response(UserPublicSerializer(user).data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    s = LoginSerializer(data=request.data)
    s.is_valid(raise_exception=True)
    user = s.validated_data["user"]
    return Response({
        "access": create_access_token(user.id),
        "refresh": create_refresh_token(user.id),
        "user": UserPublicSerializer(user).data,
    })


@api_view(["POST"])
@permission_classes([AllowAny])
def refresh_view(request):
    token = request.data.get("refresh")
    if not token:
        return Response({"detail": "refresh is required"}, status=400)

    payload = decode_token(token)
    if payload.get("type") != "refresh":
        return Response({"detail": "Refresh token required"}, status=400)

    user_id = payload.get("user_id")
    user = Users.objects.filter(id=user_id).first()
    if not user:
        return Response({"detail": "User not found"}, status=404)

    return Response({"access": create_access_token(user.id)})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me_view(request):
    return Response(UserPublicSerializer(request.user).data)



class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Categories.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]


class GoalViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Goals.objects.all()
    serializer_class = GoalSerializer
    permission_classes = [AllowAny]


class EquipmentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Equipment.objects.all()
    serializer_class = EquipmentSerializer
    permission_classes = [AllowAny]


class ExerciseViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Exercises.objects.select_related("category").all()
    serializer_class = ExerciseSerializer
    permission_classes = [AllowAny]



class WorkoutPlanViewSet(viewsets.ModelViewSet):
    serializer_class = WorkoutPlanSerializer
    lookup_field = "plan_id"

    def get_queryset(self):
        return WorkoutPlan.objects.filter(user=self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["POST"])
    def create_session(self, request, plan_id=None):
        session = create_session_from_plan(user=request.user, plan_id=int(plan_id))
        return Response(WorkoutSessionSerializer(session).data, status=201)



class WorkoutSessionViewSet(viewsets.ModelViewSet):
    serializer_class = WorkoutSessionSerializer
    lookup_field = "session_id"

    def get_queryset(self):
        return WorkoutSession.objects.filter(user=self.request.user).order_by("-date")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class SessionExerciseViewSet(viewsets.ModelViewSet):
    serializer_class = SessionExerciseSerializer
    lookup_field = "session_exercise_id"

    def get_queryset(self):
        return SessionExercise.objects.filter(session__user=self.request.user).select_related("session", "exercise")

    def perform_create(self, serializer):
        session = serializer.validated_data.get("session")
        if session.user_id != self.request.user.id:
            raise PermissionDenied("Not your session")
        serializer.save()


class SessionExerciseSetViewSet(viewsets.ModelViewSet):
    serializer_class = SessionExerciseSetSerializer
    lookup_field = "set_id"

    def get_queryset(self):
        return SessionExerciseSets.objects.filter(session_exercise__session__user=self.request.user).select_related("session_exercise")

    def perform_create(self, serializer):
        se = serializer.validated_data.get("session_exercise")
        if se.session.user_id != self.request.user.id:
            raise PermissionDenied("Not your session")
        serializer.save()
