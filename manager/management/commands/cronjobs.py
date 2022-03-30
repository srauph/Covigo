import datetime

from django.core.management.base import BaseCommand, CommandError

from status.utils import send_status_reminders


class Command(BaseCommand):
    """
    This command runs any function that is intended to be run on a schedule.
    This command is intended to be scheduled to run every hour.
    """
    help = 'Runs internal scheduled functions every hour'

    def add_arguments(self, parser):
        parser.add_argument(
            # Specify the hour to use when this command is triggered, instead of using the current hour
            '--hour',
            type=int,
            help='Specify an hour instead of using the current hour',
            required=False
        )

    def handle(self, *args, **options):
        """
        Run the scheduled functions.
        @param args: None for now
        @param options: The specified hour, if it exists.
        @return: None
        """

        # Use specified hour if it exists, else get the current hour
        if options['hour']:
            current_hour = options['hour']
        else:
            current_hour = datetime.datetime.now().hour

        # Create datetime object of today at precisely the specified hour
        current_date = datetime.datetime.combine(
            datetime.date.today(),
            datetime.time(current_hour, 0)
        )

        # Run each function
        jobs_to_run = [
            send_status_reminders,
        ]

        for job in jobs_to_run:
            try:
                job(current_date=current_date)
            except:
                raise CommandError(f"Job {job} failed to run at {datetime.datetime.now()}")
