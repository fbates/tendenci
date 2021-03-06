import commands
from django.conf import settings
from django.core.management.base import BaseCommand
from datetime import datetime

class Command(BaseCommand):
    """
    example: python manage.py expire_stories
    """
    def handle(self, *args, **kwargs):
        from stories.models import Story
        for story in Story.objects.filter(expires=True, status_detail='active'):
            if story.end_dt < datetime.now():
                story.status_detail = 'expired'
                story.save()
