import datetime

from django.core.management.base import BaseCommand, CommandError

from status.utils import send_status_reminders


class Command(BaseCommand):
    help = 'Runs internal scheduled functions every hour'

    def handle(self, *args, **options):
        jobs_to_run = [
            send_status_reminders,
        ]

        current_hour = datetime.datetime.now().hour
        current_date = datetime.datetime.combine(
            datetime.date.today(),
            datetime.time(current_hour, 0)
        )

        for job in jobs_to_run:
            try:
                job(current_date=current_date)
            except:
                raise CommandError(f"Job {job} failed to run at {datetime.datetime.now()}")
