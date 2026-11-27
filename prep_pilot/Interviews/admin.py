from django.contrib import admin
from .models import Topic, Question, InterviewSession, Answer


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    search_fields = ['name']


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['text', 'interview_type', 'topic', 'difficulty', 'is_ai_generated', 'created_by']
    list_filter = ['interview_type', 'difficulty', 'is_ai_generated', 'topic']
    search_fields = ['text']
    readonly_fields = ['created_by', 'created_at']

    def save_model(self, request, obj, form, change):
        if not change:  # only set on creation
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(InterviewSession)
class InterviewSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'interview_type', 'topic', 'difficulty', 'status', 'score']
    list_filter = ['interview_type', 'difficulty', 'status']

    def has_add_permission(self, request):
        return False  # sessions are started by interviewees via the API


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ['question', 'score', 'answered_at']

    def has_add_permission(self, request):
        return False  # answers only come from the API