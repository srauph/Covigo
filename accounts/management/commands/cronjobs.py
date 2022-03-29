import datetime

from django.core.management.base import BaseCommand, CommandError

from status.utils import send_status_reminders


class Command(BaseCommand):
    help = 'Runs the cron jobs of the system'

    def handle(self, *args, **options):
        jobs_to_run = [
            send_status_reminders,
        ]

        for job in jobs_to_run:
            try:
                job()
            except:
                raise CommandError(f"Job {job} failed to run at {datetime.datetime.now}")