#!/usr/bin/env python
"""
Script to check image status in database and file system
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.product.models import Good, Image, Category

print("=" * 50)
print("DATABASE IMAGE STATUS")
print("=" * 50)

# Count images
total_images = Image.objects.count()
print(f"\n📸 Total Images in DB: {total_images}")

# Check goods with images
goods_with_images = Good.objects.filter(product__images__isnull=False).distinct().count()
print(f"🛒 Goods with images: {goods_with_images}")

# Show sample image paths
print(f"\n📁 Sample Image Paths:")
for img in Image.objects.all()[:10]:
    print(f"  - {img.image}")

# Check categories
print(f"\n📂 Categories:")
for cat in Category.objects.all():
    print(f"  - {cat.name}: Icon={cat.icon if hasattr(cat, 'icon') else 'N/A'}")

print("\n" + "=" * 50)
print("FILE SYSTEM STATUS")
print("=" * 50)

# Check mediafiles directory
mediafiles_path = "mediafiles"
if os.path.exists(mediafiles_path):
    files = []
    for root, dirs, filenames in os.walk(mediafiles_path):
        for f in filenames:
            files.append(os.path.join(root, f))
    
    print(f"\n📂 Total files in mediafiles/: {len(files)}")
    print(f"📁 Sample files:")
    for f in files[:10]:
        print(f"  - {f}")
else:
    print(f"\n❌ Error: {mediafiles_path} directory does not exist!")

print("\n" + "=" * 50)
