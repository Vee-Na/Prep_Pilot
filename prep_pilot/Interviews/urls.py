from django.urls import path
from .views import TopicListCreateView, TopicDetailView,QuestionListCreateView, QuestionDetailView,SessionListCreateView, SessionDetailView, SubmitAnswerView


urlpatterns = [
    path('topics/', TopicListCreateView.as_view()),
    path('topics/<int:pk>/', TopicDetailView.as_view()),
    path('questions/', QuestionListCreateView.as_view()),
    path('questions/<int:pk>/', QuestionDetailView.as_view()),
    path('sessions/', SessionListCreateView.as_view()),
    path('sessions/<uuid:pk>/', SessionDetailView.as_view()),
    path('sessions/<uuid:session_id>/answers/<int:answer_id>/', SubmitAnswerView.as_view()),
]