from django.core.management.base import BaseCommand

from items.lifecycle import run_lifecycle
from items.models import GRACE_DAYS, REMIND_AFTER_DAYS


class Command(BaseCommand):
    help = "Remind posters about old posts, and take down posts whose reminder went unanswered."

    def add_arguments(self, parser):
        parser.add_argument("--remind-after", type=int, default=REMIND_AFTER_DAYS,
                            help="Days before a post gets a reminder (default %(default)s)")
        parser.add_argument("--grace", type=int, default=GRACE_DAYS,
                            help="Days to answer a reminder before the post comes down (default %(default)s)")
        parser.add_argument("--dry-run", action="store_true",
                            help="Only count what would happen. Send and change nothing.")

    def handle(self, *args, **options):
        r = run_lifecycle(
            remind_after=options["remind_after"],
            grace=options["grace"],
            dry_run=options["dry_run"],
        )
        label = "DRY RUN, nothing changed. Would" if options["dry_run"] else "Done."
        self.stdout.write(self.style.SUCCESS(
            f"{label} reminders: {r['reminded']}, taken down: {r['expired']}, "
            f"email failures: {r['failed']}."
        ))