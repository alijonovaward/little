import os
from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.customer.models import Banner
from apps.product.models import Category, Image, ProductItem


IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}


def _iter_images(folder: Path) -> list[Path]:
    if not folder.exists():
        return []
    files: list[Path] = []
    for path in folder.rglob("*"):
        if path.is_file() and path.suffix.lower() in IMAGE_EXTS:
            files.append(path)
    return sorted(files, key=lambda p: p.name.lower())


class Command(BaseCommand):
    help = (
        "Import images from a TEST SOURCE folder into the database. "
        "Works with local MEDIA_ROOT or Cloudinary (when CLOUDINARY_URL is configured)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--root",
            required=True,
            help="Path containing BANNER/, CATEGORY/, PRODUCT/ subfolders.",
        )
        parser.add_argument(
            "--categories",
            action="store_true",
            help="Assign images to Category.image in ID order.",
        )
        parser.add_argument(
            "--products",
            action="store_true",
            help=(
                "Attach images to ProductItem via apps.product.models.Image (1 image per ProductItem). "
                "Targets ProductItem rows that have related goods/phones/tickets."
            ),
        )
        parser.add_argument(
            "--banners",
            action="store_true",
            help="Create/update Banner records and attach images (1 per banner).",
        )
        parser.add_argument(
            "--clear-existing",
            action="store_true",
            help="Clear existing images for the selected targets before importing.",
        )
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Actually write changes. Without this flag the command only prints what it would do.",
        )

    def handle(self, *args, **options):
        root = Path(options["root"]).expanduser().resolve()
        do_apply: bool = bool(options["apply"])

        if not root.exists():
            raise SystemExit(f"Root folder not found: {root}")

        selected = [k for k in ("categories", "products", "banners") if options.get(k)]
        if not selected:
            raise SystemExit("Select at least one target: --categories, --products, or --banners")

        category_files = _iter_images(root / "CATEGORY")
        product_files = _iter_images(root / "PRODUCT")
        banner_files = _iter_images(root / "BANNER")

        self.stdout.write(self.style.NOTICE(f"Root: {root}"))
        self.stdout.write(
            self.style.NOTICE(
                f"Found files: CATEGORY={len(category_files)}, PRODUCT={len(product_files)}, BANNER={len(banner_files)}"
            )
        )

        if not do_apply:
            self.stdout.write(self.style.WARNING("DRY RUN: no changes will be saved (use --apply to write)."))

        # Only wrap in a transaction when we are actually applying changes.
        # Note: storage writes (Cloudinary/local FS) happen as part of field save.
        ctx = transaction.atomic() if do_apply else _NoopContext()
        with ctx:
            if options.get("categories"):
                self._import_categories(category_files, clear_existing=options["clear_existing"], apply=do_apply)

            if options.get("products"):
                self._import_products(product_files, clear_existing=options["clear_existing"], apply=do_apply)

            if options.get("banners"):
                self._import_banners(banner_files, clear_existing=options["clear_existing"], apply=do_apply)

        self.stdout.write(self.style.SUCCESS("Import complete." if do_apply else "Dry run complete."))

    def _import_categories(self, files: list[Path], *, clear_existing: bool, apply: bool) -> None:
        categories = list(Category.objects.all().order_by("id"))
        self.stdout.write(self.style.NOTICE(f"Categories in DB: {len(categories)}"))
        if not files:
            self.stdout.write(self.style.WARNING("No CATEGORY images found."))
            return

        count = min(len(categories), len(files))
        self.stdout.write(self.style.NOTICE(f"Will assign {count} category images (by ID order)."))

        for category, image_path in zip(categories[:count], files[:count], strict=False):
            action = "set"
            if clear_existing and category.image:
                action = "replace"

            self.stdout.write(f"Category id={category.id} name={category.name!r}: {action} <- {image_path.name}")
            if not apply:
                continue

            with image_path.open("rb") as fh:
                category.image.save(image_path.name, File(fh), save=True)

    def _import_products(self, files: list[Path], *, clear_existing: bool, apply: bool) -> None:
        # Target ProductItem rows that represent actual products.
        queryset = ProductItem.objects.filter(
            goods__isnull=False
        ).order_by("id")
        product_items = list(queryset)

        # If there are no goods, fall back to any ProductItem that has phones/tickets.
        if not product_items:
            product_items = list(
                ProductItem.objects.filter(
                    phones__isnull=False
                ).order_by("id")
            )
        if not product_items:
            product_items = list(
                ProductItem.objects.filter(
                    tickets__isnull=False
                ).order_by("id")
            )

        self.stdout.write(self.style.NOTICE(f"ProductItem targets: {len(product_items)}"))
        if not files:
            self.stdout.write(self.style.WARNING("No PRODUCT images found."))
            return

        if clear_existing and apply:
            Image.objects.filter(product_id__in=[p.id for p in product_items]).delete()
            self.stdout.write(self.style.WARNING("Cleared existing ProductItem images for target items."))

        count = min(len(product_items), len(files))
        self.stdout.write(self.style.NOTICE(f"Will attach {count} product images (1 per ProductItem, by ID order)."))

        for product_item, image_path in zip(product_items[:count], files[:count], strict=False):
            self.stdout.write(f"ProductItem id={product_item.id}: attach <- {image_path.name}")
            if not apply:
                continue

            with image_path.open("rb") as fh:
                img = Image(product=product_item, name=image_path.stem)
                img.image.save(image_path.name, File(fh), save=True)

    def _import_banners(self, files: list[Path], *, clear_existing: bool, apply: bool) -> None:
        self.stdout.write(self.style.NOTICE("Importing banners..."))
        if not files:
            self.stdout.write(self.style.WARNING("No BANNER images found."))
            return

        if clear_existing and apply:
            Banner.objects.all().delete()
            self.stdout.write(self.style.WARNING("Cleared existing banners."))

        for idx, image_path in enumerate(files, start=1):
            self.stdout.write(f"Banner #{idx}: set <- {image_path.name}")
            if not apply:
                continue

            banner = Banner.objects.create(active=True, title=f"Banner {idx}")
            with image_path.open("rb") as fh:
                banner.image.save(image_path.name, File(fh), save=True)


class _NoopContext:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False
