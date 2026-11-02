from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand

from items.images import shrink_image
from items.models import Item

SKIP_BELOW = 300 * 1024   # photos already under 300 KB are left alone


class Command(BaseCommand):
    help = "Shrink photos that were uploaded before automatic shrinking existed."

    def handle(self, *args, **options):
        shrunk = skipped = failed = 0
        saved_bytes = 0

        for item in Item.objects.exclude(image=""):
            try:
                old = item.image
                old_name, old_size = old.name, old.size
                if old_size < SKIP_BELOW:
                    skipped += 1
                    continue

                new_file = shrink_image(old)
                if new_file.size >= old_size:
                    skipped += 1
                    continue

                item.image.save(new_file.name, new_file, save=False)
                # .update() leaves the post's "updated" time alone.
                Item.objects.filter(pk=item.pk).update(image=item.image.name)
                if old_name != item.image.name:
                    default_storage.delete(old_name)

                saved_bytes += old_size - new_file.size
                shrunk += 1
            except Exception as e:   # a missing or broken file must not stop the rest
                failed += 1
                self.stderr.write(f"Item {item.pk}: {e}")

        self.stdout.write(self.style.SUCCESS(
            f"Shrunk {shrunk}, skipped {skipped}, failed {failed}. "
            f"Saved {saved_bytes // 1024} KB."
        ))