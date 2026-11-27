from django.conf import settings
from django.db import models
import uuid
from django.core.exceptions import ValidationError


class InterviewType(models.TextChoices):
    TECHNICAL = 'technical', 'Technical'
    HR = 'HR', 'HR'
    BEHAVIORAL = 'Behavioral', 'Behavioral'


class Difficulty(models.TextChoices):
    EASY = 'Easy', 'Easy'
    MEDIUM = 'Medium', 'Medium'
    HARD = 'Hard', 'Hard'


class SessionStatus(models.TextChoices):
    IN_PROGRESS = 'In_progress', 'In progress'
    COMPLETED = 'Completed', 'Completed'


class Topic(models.Model):
    name = models.CharField(max_length=100, unique=True)  

    class Meta:
        verbose_name='Topics'
        verbose_name_plural='Topics'

    def __str__(self):
        return self.name


class Question(models.Model):
    text = models.TextField()
    # topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='questions')
    interview_type = models.CharField(max_length=20, choices=InterviewType.choices)
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True, blank=True)
    difficulty = models.CharField(max_length=10, choices=Difficulty.choices)
    is_ai_generated = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='created_questions',
        limit_choices_to={'role': 'admin'}
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        super().clean()
        if self.interview_type == "technical" and not self.topic:
            raise ValidationError({"topic": "Topic is required for technical questions."})

    class Meta:
        verbose_name='Questions'
        verbose_name_plural='Questions'

    def __str__(self):
        return f'{self.interview_type} | {self.topic} | {self.difficulty} | {self.text[:50]}'


class InterviewSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sessions'
    )
    # topic = models.ForeignKey(Topic, on_delete=models.PROTECT)
    interview_type = models.CharField(max_length=20, choices=InterviewType.choices)
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True, blank=True)
    difficulty = models.CharField(max_length=10, choices=Difficulty.choices)
    status = models.CharField(
        max_length=20, choices=SessionStatus.choices, default=SessionStatus.IN_PROGRESS
    )
    score = models.FloatField(null=True, blank=True)  # overall, filled when completed
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def clean(self):
        super().clean()
        if self.interview_type == "technical" and not self.topic:
            raise ValidationError({"topic": "Topic is required for technical interviews."})

    class Meta:
        ordering = ['-started_at']
        verbose_name='Interview_sessions'
        verbose_name_plural='Interview_sessions'


    def __str__(self):
        return f'{self.user} | {self.interview_type} | {self.topic} | {self.status}'


class Answer(models.Model):
    session = models.ForeignKey(InterviewSession, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.PROTECT)
    answer_text = models.TextField(blank=True)
    score = models.FloatField(null=True, blank=True)   # per-question score from the LLM
    feedback = models.TextField(blank=True)            # LLM feedback
    answered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering=['id']
        unique_together = ('session', 'question')
        verbose_name='Answers'
        verbose_name_plural='Answers'

    def __str__(self):
        return f'Session {self.session_id} | Q{self.question_id}'