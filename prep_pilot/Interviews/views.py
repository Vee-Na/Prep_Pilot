import random
from django.db import transaction
from django.db.models import ProtectedError, Avg
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from authentication.models import Role
from authentication.permissions import IsAdmin, IsInterviewee
from .models import Topic, Question, InterviewSession, Answer, SessionStatus
from .serializer import TopicSerializer, QuestionSerializer,SessionCreateSerializer, SessionSerializer, SessionDetailSerializer,AnswerSerializer, AnswerSubmitSerializer
from .scoring import evaluate_answer


# ---------------------------------------------------------------- topics

class TopicListCreateView(APIView):
    serializer_class = TopicSerializer

    def get_permissions(self):
        # any logged-in user can list topics, only admin can create
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [IsAuthenticated()]

    def get(self, request, *args, **kwargs):
        topics = Topic.objects.all().order_by('name')
        serializer = self.serializer_class(topics, many=True)
        return Response(serializer.data, status=200)

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)

        return Response(serializer.errors, status=400)


class TopicDetailView(APIView):
    permission_classes = [IsAdmin]
    serializer_class = TopicSerializer

    def get_object(self, pk):
        return Topic.objects.filter(pk=pk).first()

    def put(self, request, pk, *args, **kwargs):
        topic = self.get_object(pk)

        if not topic:
            return Response({'msg': 'topic not found'}, status=404)

        serializer = self.serializer_class(topic, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)

        return Response(serializer.errors, status=400)

    def delete(self, request, pk, *args, **kwargs):
        topic = self.get_object(pk)

        if not topic:
            return Response({'msg': 'topic not found'}, status=404)

        try:
            topic.delete()
        except ProtectedError:
            return Response(
                {'msg': 'topic is used in interview sessions and cannot be deleted'},
                status=400,
            )

        return Response({'msg': 'topic deleted'}, status=200)


# ------------------------------------------------------------- questions

class QuestionListCreateView(APIView):
    permission_classes = [IsAdmin]
    serializer_class = QuestionSerializer

    def get(self, request, *args, **kwargs):
        questions = Question.objects.select_related('topic').order_by('-created_at')

        # optional filters: ?topic=1&interview_type=Technical&difficulty=Easy
        topic = request.query_params.get('topic')
        interview_type = request.query_params.get('interview_type')
        difficulty = request.query_params.get('difficulty')

        if topic:
            questions = questions.filter(topic_id=topic)
        if interview_type:
            questions = questions.filter(interview_type=interview_type)
        if difficulty:
            questions = questions.filter(difficulty=difficulty)

        serializer = self.serializer_class(questions, many=True)
        return Response(serializer.data, status=200)

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            serializer.save(created_by=request.user, is_ai_generated=False)
            return Response(serializer.data, status=201)

        return Response(serializer.errors, status=400)


class QuestionDetailView(APIView):
    permission_classes = [IsAdmin]
    serializer_class = QuestionSerializer

    def get_object(self, pk):
        return Question.objects.filter(pk=pk).first()

    def get(self, request, pk, *args, **kwargs):
        question = self.get_object(pk)

        if not question:
            return Response({'msg': 'question not found'}, status=404)

        return Response(self.serializer_class(question).data, status=200)

    def put(self, request, pk, *args, **kwargs):
        question = self.get_object(pk)

        if not question:
            return Response({'msg': 'question not found'}, status=404)

        serializer = self.serializer_class(question, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)

        return Response(serializer.errors, status=400)

    def delete(self, request, pk, *args, **kwargs):
        question = self.get_object(pk)

        if not question:
            return Response({'msg': 'question not found'}, status=404)

        try:
            question.delete()
        except ProtectedError:
            return Response(
                {'msg': 'question is used in past sessions and cannot be deleted'},
                status=400,
            )

        return Response({'msg': 'question deleted'}, status=200)


# -------------------------------------------------------------- sessions

class SessionListCreateView(APIView):

    def get_permissions(self):
        # admin and interviewee can list, only interviewee can start a session
        if self.request.method == 'POST':
            return [IsInterviewee()]
        return [(IsInterviewee | IsAdmin)()]

    def get(self, request, *args, **kwargs):
        sessions = InterviewSession.objects.select_related('topic', 'user')

        # interviewees see only their own sessions, admins see all
        if request.user.role != Role.ADMIN:
            sessions = sessions.filter(user=request.user)

        serializer = SessionSerializer(sessions, many=True)
        return Response(serializer.data, status=200)

    def post(self, request, *args, **kwargs):
        serializer = SessionCreateSerializer(data=request.data)

        if serializer.is_valid():

            data = serializer.validated_data
            num_questions = data.get('num_questions', 5)

            question_ids = list(
                Question.objects.filter(
                    topic=data['topic'],
                    interview_type=data['interview_type'],
                    difficulty=data['difficulty'],
                ).values_list('id', flat=True)
            )

            # never ask for more questions than the bank has
            chosen = random.sample(question_ids, min(num_questions, len(question_ids)))

            with transaction.atomic():
                session = serializer.save(user=request.user)
                Answer.objects.bulk_create(
                    [Answer(session=session, question_id=qid) for qid in chosen]
                )

            return Response(SessionDetailSerializer(session).data, status=201)

        return Response(serializer.errors, status=400)


class SessionDetailView(APIView):
    permission_classes = [IsInterviewee | IsAdmin]

    def get(self, request, pk, *args, **kwargs):
        sessions = (
            InterviewSession.objects
            .filter(pk=pk)
            .select_related('topic', 'user')
            .prefetch_related('answers__question')
        )

        # interviewees can open only their own sessions, admins can open any
        if request.user.role != Role.ADMIN:
            sessions = sessions.filter(user=request.user)

        session = sessions.first()

        if not session:
            return Response({'msg': 'session not found'}, status=404)

        return Response(SessionDetailSerializer(session).data, status=200)


# --------------------------------------------------------------- answers

class SubmitAnswerView(APIView):
    permission_classes = [IsInterviewee]

    def post(self, request, session_id, answer_id, *args, **kwargs):

        answer = (
            Answer.objects
            .select_related('session', 'question')
            .filter(pk=answer_id, session_id=session_id, session__user=request.user)
            .first()
        )

        if not answer:
            return Response({'msg': 'answer not found'}, status=404)

        session = answer.session

        if session.status == SessionStatus.COMPLETED:
            return Response({'msg': 'this session is already completed'}, status=400)

        if answer.answered_at:
            return Response({'msg': 'this question is already answered'}, status=400)

        serializer = AnswerSubmitSerializer(answer, data=request.data)

        if serializer.is_valid():

            # 1. save the user's answer text
            answer = serializer.save(answered_at=timezone.now())

            # 2. score it (placeholder now, LLM later)
            score, feedback = evaluate_answer(answer.question.text, answer.answer_text)
            answer.score = score
            answer.feedback = feedback
            answer.save(update_fields=['score', 'feedback'])

            # 3. if every question is answered, finish the session
            session_completed = False
            if not session.answers.filter(answered_at__isnull=True).exists():
                average = session.answers.aggregate(avg=Avg('score'))['avg']
                session.score = round(average or 0, 2)
                session.status = SessionStatus.COMPLETED
                session.completed_at = timezone.now()
                session.save(update_fields=['score', 'status', 'completed_at'])
                session_completed = True

            data = AnswerSerializer(answer).data
            data['session_completed'] = session_completed
            data['session_score'] = session.score

            return Response(data, status=200)

        return Response(serializer.errors, status=400)