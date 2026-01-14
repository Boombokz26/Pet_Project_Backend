from rest_framework.routers import DefaultRouter
from .views import UsersViewSet, WorkoutSessionViewSet, SessionExerciseViewSet, SessionExerciseSetsViewSet

router = DefaultRouter()
router.register(r"users", UsersViewSet)
router.register(r"sessions", WorkoutSessionViewSet)
router.register(r"session-exercises", SessionExerciseViewSet)
router.register(r"sets", SessionExerciseSetsViewSet)

urlpatterns = router.urls
