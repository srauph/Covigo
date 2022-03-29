import datetime

from django.core.management.base import BaseCommand, CommandError

from status.utils import send_status_reminder


class Command(BaseCommand):
    help = 'Runs internal scheduled functions every hour'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hour',
            type=int,
            help='Specify an hour instead of using the current hour',
            required=False
        )

    def handle(self, *args, **options):
        jobs_to_run = [
            send_status_reminder,
        ]

        if options['hour']:
            current_hour = options['hour']
        else:
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
