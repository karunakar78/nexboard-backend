from rest_framework import serializers
from apps.accounts.serializers import UserSerializer
from .models import ActivityLog, Comment, Label, Task


class LabelSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Label
        fields = ['id', 'name', 'color']
        read_only_fields = ['id']


class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model  = Comment
        fields = ['id', 'author', 'content', 'created_at', 'updated_at']
        read_only_fields = ['id', 'author', 'created_at', 'updated_at']


class ActivityLogSerializer(serializers.ModelSerializer):
    actor = UserSerializer(read_only=True)

    class Meta:
        model  = ActivityLog
        fields = ['id', 'actor', 'verb', 'old_value', 'new_value', 'created_at']


class SubTaskSerializer(serializers.ModelSerializer):
    """Lightweight serializer for subtasks nested inside a parent task."""
    assignee = UserSerializer(read_only=True)

    class Meta:
        model  = Task
        fields = ['id', 'title', 'status', 'priority', 'assignee', 'due_date']


class TaskSerializer(serializers.ModelSerializer):
    assignee    = UserSerializer(read_only=True)
    assignee_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    created_by  = UserSerializer(read_only=True)
    labels      = LabelSerializer(many=True, read_only=True)
    label_ids   = serializers.ListField(
        child=serializers.UUIDField(), write_only=True, required=False
    )
    subtasks        = SubTaskSerializer(many=True, read_only=True)
    comment_count   = serializers.SerializerMethodField()

    class Meta:
        model  = Task
        fields = [
            'id', 'title', 'description', 'status', 'priority',
            'assignee', 'assignee_id', 'created_by',
            'labels', 'label_ids', 'due_date',
            'parent', 'subtasks', 'comment_count',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def get_comment_count(self, obj):
        return obj.comments.count()

    def create(self, validated_data):
        label_ids  = validated_data.pop('label_ids', [])
        assignee_id = validated_data.pop('assignee_id', None)

        task = Task.objects.create(
            **validated_data,
            assignee_id=assignee_id,
            created_by=self.context['request'].user,
            project=self.context['project'],
        )
        if label_ids:
            task.labels.set(label_ids)

        # Log the creation
        ActivityLog.objects.create(
            task=task,
            actor=self.context['request'].user,
            verb='created this task',
        )
        return task

    def update(self, instance, validated_data):
        label_ids   = validated_data.pop('label_ids', None)
        assignee_id = validated_data.pop('assignee_id', None)

        # Track field changes for the activity log
        tracked = ['status', 'priority', 'assignee_id', 'due_date']
        logs = []
        for field in tracked:
            old = str(getattr(instance, field) or '')
            new = str(validated_data.get(field, getattr(instance, field)) or '')
            if old != new:
                logs.append(ActivityLog(
                    task=instance,
                    actor=self.context['request'].user,
                    verb=f'changed {field.replace("_id", "")} from "{old}" to "{new}"',
                    old_value=old,
                    new_value=new,
                ))

        if assignee_id is not None:
            instance.assignee_id = assignee_id

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if label_ids is not None:
            instance.labels.set(label_ids)

        if logs:
            ActivityLog.objects.bulk_create(logs)

        return instance