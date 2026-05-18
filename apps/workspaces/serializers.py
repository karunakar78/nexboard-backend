import secrets
from datetime import timedelta

from django.utils import timezone
from django.utils.text import slugify
from rest_framework import serializers

from apps.accounts.serializers import UserSerializer
from .models import Workspace, WorkspaceInvite, WorkspaceMember


class WorkspaceMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model  = WorkspaceMember
        fields = ['id', 'user', 'role', 'created_at']


class WorkspaceSerializer(serializers.ModelSerializer):
    owner        = UserSerializer(read_only=True)
    member_count = serializers.SerializerMethodField()
    my_role      = serializers.SerializerMethodField()

    class Meta:
        model  = Workspace
        fields = [
            'id', 'name', 'slug', 'description',
            'owner', 'member_count', 'my_role', 'created_at',
        ]
        read_only_fields = ['id', 'slug', 'owner', 'created_at']

    def get_member_count(self, obj):
        return obj.members.count()

    def get_my_role(self, obj):
        request = self.context.get('request')
        if not request:
            return None
        membership = obj.members.filter(user=request.user).first()
        return membership.role if membership else None

    def create(self, validated_data):
        # Auto-generate slug from name, ensure uniqueness
        base_slug = slugify(validated_data['name'])
        slug = base_slug
        counter = 1
        while Workspace.objects.filter(slug=slug).exists():
            slug = f'{base_slug}-{counter}'
            counter += 1

        workspace = Workspace.objects.create(
            **validated_data,
            slug=slug,
            owner=self.context['request'].user,
        )
        # Creator is automatically the owner-member
        WorkspaceMember.objects.create(
            workspace=workspace,
            user=self.context['request'].user,
            role=WorkspaceMember.Role.OWNER,
        )
        return workspace


class InviteMemberSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role  = serializers.ChoiceField(
        choices=WorkspaceMember.Role.choices,
        default=WorkspaceMember.Role.MEMBER,
    )

    def validate_email(self, value):
        workspace = self.context['workspace']
        if WorkspaceMember.objects.filter(
            workspace=workspace,
            user__email=value,
        ).exists():
            raise serializers.ValidationError(
                'This user is already a member of the workspace.'
            )
        return value

    def create(self, validated_data):
        workspace = self.context['workspace']
        inviter   = self.context['request'].user

        # Upsert: re-invite if a previous invite exists
        invite, _ = WorkspaceInvite.objects.update_or_create(
            workspace=workspace,
            email=validated_data['email'],
            defaults={
                'invited_by': inviter,
                'role':       validated_data['role'],
                'token':      secrets.token_hex(32),
                'status':     WorkspaceInvite.Status.PENDING,
                'expires_at': timezone.now() + timedelta(days=7),
            },
        )
        return invite


class UpdateMemberRoleSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=WorkspaceMember.Role.choices)