import json

from django.core.management.base import BaseCommand, CommandError

from accounts.models import User


class Command(BaseCommand):
    help = (
        "Import users from a Django dumpdata JSON file. Adds new users, skips "
        "existing ones, and never grants admin rights."
    )

    def add_arguments(self, parser):
        parser.add_argument("path", help="Path to the users JSON file")

    def handle(self, *args, **options):
        try:
            with open(options["path"], encoding="utf-8-sig") as f:
                records = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            raise CommandError(f"Could not read the file: {exc}")

        created = 0
        skipped = 0

        for rec in records:
            if rec.get("model") != "accounts.user":
                continue
            fields = rec["fields"]
            id_number = fields["id_number"].strip().upper()

            # Never overwrite someone who already exists.
            if User.objects.filter(id_number__iexact=id_number).exists():
                self.stdout.write(f"SKIP (already exists): {id_number}")
                skipped += 1
                continue

            User(
                id_number=id_number,
                password=fields["password"],       # already hashed; copied as it is
                first_name=fields["first_name"],
                last_name=fields["last_name"],
                email=fields["email"],
                is_active=fields["is_active"],
                is_staff=False,                    # no admin rights imported
                is_superuser=False,
                date_joined=fields["date_joined"],
                last_login=fields["last_login"],
            ).save()
            self.stdout.write(f"CREATED: {id_number}")
            created += 1

        self.stdout.write(self.style.SUCCESS(
            f"Done. created = {created}, skipped = {skipped}"
        ))