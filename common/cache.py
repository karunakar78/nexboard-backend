from django.core.cache import cache


def invalidate_workspace_analytics(workspace_id):
    """
    Call this whenever tasks or projects change in a workspace.
    Django's cache_page key includes the URL — we use a pattern delete.
    For production, switch to cache.delete_pattern() with django-redis.
    """
    pattern = f'*workspaces*{workspace_id}*analytics*'
    try:
        cache.delete_pattern(pattern)
    except AttributeError:
        # Local memory cache doesn't support patterns — skip silently
        pass