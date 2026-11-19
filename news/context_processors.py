from django.db import DatabaseError

from .models import Notification


def notification_badge(request):
    try:
        unread_count = Notification.objects.filter(read_at__isnull=True).count()
    except DatabaseError:
        # The navigation must also render when displaying a database error.
        unread_count = 0
    return {"unread_notification_count": unread_count}
