from rest_framework import serializers
from apps.accounts.serializers import UserSerializer
from apps.workspaces.models import WorkspaceMember
from .models import Project


class ProjectSerializer(serializers.ModelSerializer):
    lead         = UserSerializer(read_only=True)
    lead_id      = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    task_count   = serializers.SerializerMethodField()
    workspace_id = serializers.UUIDField(read_only=True)

    class Meta:
        model  = Project
        fields = [
            'id', 'workspace_id', 'name', 'description',
            'status', 'visibility', 'lead', 'lead_id',
            'task_count', 'created_at',
        ]
        read_only_fields = ['id', 'workspace_id', 'created_at']

    def get_task_count(self, obj):
        return 0

    def validate_lead_id(self, value):
        if value is None:
            return value
        workspace = self.context['workspace']
        # Lead must be a member of the workspace
        if not WorkspaceMember.objects.filter(
            workspace=workspace, user_id=value
        ).exists():
            raise serializers.ValidationError(
                'Lead must be a member of the workspace.'
            )
        return value

    def create(self, validated_data):
        lead_id = validated_data.pop('lead_id', None)
        project = Project.objects.create(
            workspace=self.context['workspace'],
            lead_id=lead_id,
            **validated_data,
        )
        return project

    def update(self, instance, validated_data):
        lead_id = validated_data.pop('lead_id', None)
        if lead_id is not None:
            instance.lead_id = lead_id
        return super().update(instance, validated_data)