import csv

from django.core.management.base import BaseCommand, CommandError

from accounts.models import RosterEntry


class Command(BaseCommand):
    help = "Import registration numbers from a CSV file: number[,name] on each row."

    def add_arguments(self, parser):
        parser.add_argument("path", help="Path to the CSV file")

    def handle(self, *args, **options):
        try:
            f = open(options["path"], newline="", encoding="utf-8-sig")
        except OSError as e:
            raise CommandError(f"Can't open the file: {e}")

        created = skipped = 0
        with f:
            for row in csv.reader(f):
                if not row or not row[0].strip():
                    continue
                number = row[0].strip().upper()
                if number in ("NUMBER", "REG NO", "REG_NO", "REGISTRATION NUMBER"):
                    continue   # a header row
                name = row[1].strip() if len(row) > 1 else ""
                _entry, was_created = RosterEntry.objects.get_or_create(
                    number=number, defaults={"name": name}
                )
                if was_created:
                    created += 1
                else:
                    skipped += 1

        self.stdout.write(self.style.SUCCESS(
            f"Added {created} numbers, skipped {skipped} already on the roster."
        ))