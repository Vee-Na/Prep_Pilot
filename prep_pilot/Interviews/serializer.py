from rest_framework import serializers
from .models import Topic, Question, InterviewSession, Answer


class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = ['id', 'name']


class QuestionSerializer(serializers.ModelSerializer):
    topic_name = serializers.CharField(source='topic.name', read_only=True, allow_null=True)  # CHANGED: allow_null

    class Meta:
        model = Question
        fields = [
            'id', 'text', 'topic', 'topic_name', 'interview_type',
            'difficulty', 'is_ai_generated', 'created_by', 'created_at',
        ]
        read_only_fields = ['is_ai_generated', 'created_by', 'created_at']

    def validate(self, attrs):
        interview_type = attrs.get('interview_type', getattr(self.instance, 'interview_type', None))
        topic = attrs.get('topic', getattr(self.instance, 'topic', None))

        if interview_type == 'technical' and not topic:
            raise serializers.ValidationError(
                {'topic': 'Topic is required for technical questions.'}
            )
        return attrs


class SessionCreateSerializer(serializers.ModelSerializer):
    # Used when an interviewee starts a session.
    num_questions = serializers.IntegerField(
        write_only=True, default=5, min_value=1, max_value=20
    )

    class Meta:
        model = InterviewSession
        fields = ['topic', 'interview_type', 'difficulty', 'num_questions']

    def validate(self, attrs):
        # CHANGED: whole method
        interview_type = attrs['interview_type']
        topic = attrs.get('topic')

        # topic is only meaningful for technical interviews
        if interview_type == 'technical' and not topic:
            raise serializers.ValidationError(
                {'topic': 'Topic is required for technical interviews.'}
            )
        if interview_type != 'technical':
            attrs['topic'] = None  # ignore any topic sent for HR/behavioral

        # make sure the question bank has something to ask
        questions = Question.objects.filter(
            interview_type=interview_type,
            difficulty=attrs['difficulty'],
        )
        if attrs['topic']:
            questions = questions.filter(topic=attrs['topic'])

        if not questions.exists():
            raise serializers.ValidationError(
                'No questions available for this selection.'
            )

        return attrs

    def create(self, validated_data):
        # num_questions is not a model field, so the view reads it before saving
        validated_data.pop('num_questions', None)
        return super().create(validated_data)


class SessionSerializer(serializers.ModelSerializer):
    # Used for the past sessions list.
    topic_name = serializers.CharField(source='topic.name', read_only=True, allow_null=True)  # CHANGED: allow_null

    class Meta:
        model = InterviewSession
        fields = [
            'id', 'topic', 'topic_name', 'interview_type', 'difficulty',
            'status', 'score', 'started_at', 'completed_at',
        ]
        read_only_fields = fields


class AnswerSerializer(serializers.ModelSerializer):
    # Used to show a question inside a session, with user's answer and feedback.
    question_text = serializers.CharField(source='question.text', read_only=True)

    class Meta:
        model = Answer
        fields = [
            'id', 'question', 'question_text', 'answer_text',
            'score', 'feedback', 'answered_at',
        ]
        read_only_fields = fields


class AnswerSubmitSerializer(serializers.ModelSerializer):
    # Used when the interviewee submits their answer.
    class Meta:
        model = Answer
        fields = ['answer_text']
        extra_kwargs = {'answer_text': {'required': True, 'allow_blank': False}}


class SessionDetailSerializer(serializers.ModelSerializer):
    # Used to open one session
    topic_name = serializers.CharField(source='topic.name', read_only=True, allow_null=True)  # CHANGED: allow_null
    answers = AnswerSerializer(many=True, read_only=True)

    class Meta:
        model = InterviewSession
        fields = [
            'id', 'topic', 'topic_name', 'interview_type', 'difficulty',
            'status', 'score', 'started_at', 'completed_at', 'answers',
        ]
        read_only_fields = fields