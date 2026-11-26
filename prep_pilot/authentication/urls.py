from django.urls import path
from .views import LoginView, UserRegisterView, WhoAmIView

urlpatterns = [
    path('register/', UserRegisterView.as_view()),
    path('login/', LoginView.as_view()),
    path('me/', WhoAmIView.as_view())
]