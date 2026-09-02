"""
Management command: creates a default admin account and minimal demo data
so `docker-compose up --build` produces an immediately testable system.
Run: python manage.py seed_demo_data
"""
from decimal import Decimal
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.users.models import User
from apps.sellers.models import Seller
from apps.customers.models import Customer
from apps.catalog.models import Category, Product, ProductVariant, ProductSellerAssignment


class Command(BaseCommand):
    help = "Seeds a default admin account plus minimal demo catalog data."

    @transaction.atomic
    def handle(self, *args, **options):
        admin_email = settings.DEFAULT_ADMIN_EMAIL
        if not User.objects.filter(email=admin_email).exists():
            User.objects.create_superuser(email=admin_email, password="ChangeMe123!")
            self.stdout.write(self.style.SUCCESS(f"Created admin: {admin_email} / ChangeMe123!"))
        else:
            self.stdout.write("Admin already exists, skipping.")

        if not User.objects.filter(email="seller-demo@example.com").exists():
            seller_user = User.objects.create_user(
                email="seller-demo@example.com", password="SellerPass123!", role=User.Role.SELLER
            )
            seller = Seller.objects.create(
                user=seller_user, business_name="Demo Store",
                first_name="Demo", last_name="Seller", status=Seller.Status.ACTIVE,
            )
            self.stdout.write(self.style.SUCCESS("Created demo seller: seller-demo@example.com / SellerPass123!"))
        else:
            seller = Seller.objects.get(user__email="seller-demo@example.com")

        if not User.objects.filter(email="customer-demo@example.com").exists():
            customer_user = User.objects.create_user(
                email="customer-demo@example.com", password="CustomerPass123!", role=User.Role.CUSTOMER
            )
            Customer.objects.create(user=customer_user, first_name="Demo", last_name="Customer")
            self.stdout.write(self.style.SUCCESS("Created demo customer: customer-demo@example.com / CustomerPass123!"))

        categories = {
            "Electronics": "Phones, audio, and gadgets",
            "Apparel": "Everyday clothing and accessories",
            "Home & Kitchen": "Cookware, decor, and household goods",
            "Sporting Goods": "Gear for training and the outdoors",
            "Books": "Fiction, non-fiction, and reference",
        }
        category_objs = {}
        for name, desc in categories.items():
            slug = name.lower().replace(" & ", "-").replace(" ", "-")
            # Include archived rows: the default manager hides them, which
            # previously let an archived Electronics row trigger its unique
            # constraint on a repeated seed run.
            cat, _ = Category.all_objects.get_or_create(name=name, defaults={"slug": slug, "description": desc})
            if cat.is_deleted:
                cat.restore()
            if cat.status != Category.Status.ACTIVE:
                cat.status = Category.Status.ACTIVE
                cat.save(update_fields=["status"])
            category_objs[name] = cat

        demo_products = [
            ("Wireless Headphones", "Electronics", "Noise-cancelling over-ear headphones with 30-hour battery life.", Decimal("79.99"), "WH-BLACK-01", {"color": "Black"}, 50),
            ("Smart Fitness Watch", "Electronics", "Tracks heart rate, sleep, and workouts with a 7-day battery.", Decimal("129.00"), "SFW-BLUE-01", {"color": "Blue"}, 40),
            ("Portable Bluetooth Speaker", "Electronics", "Compact waterproof speaker with rich bass.", Decimal("45.50"), "PBS-RED-01", {"color": "Red"}, 60),
            ("Classic Cotton T-Shirt", "Apparel", "Soft, breathable everyday crewneck tee.", Decimal("19.99"), "CCT-WHT-M", {"size": "M", "color": "White"}, 100),
            ("Denim Jacket", "Apparel", "Mid-weight jacket with a timeless cut.", Decimal("64.00"), "DJ-BLU-L", {"size": "L", "color": "Indigo"}, 35),
            ("Running Shoes", "Apparel", "Lightweight cushioned shoes built for daily miles.", Decimal("89.99"), "RS-GRY-42", {"size": "42", "color": "Grey"}, 45),
            ("Ceramic Coffee Mug Set", "Home & Kitchen", "Set of 4 stoneware mugs, dishwasher safe.", Decimal("24.99"), "CCM-SET-4", {"pieces": "4"}, 70),
            ("Non-Stick Frying Pan", "Home & Kitchen", "10-inch pan with even heat distribution.", Decimal("34.50"), "NSFP-10IN", {"size": "10in"}, 55),
            ("Yoga Mat", "Sporting Goods", "Extra-thick non-slip mat for home workouts.", Decimal("29.99"), "YM-PURP-01", {"color": "Purple"}, 65),
            ("Adjustable Dumbbell Set", "Sporting Goods", "Space-saving pair, 5–25 lbs each.", Decimal("149.00"), "ADS-25LB", {"max_weight": "25lb"}, 20),
            ("The Art of Clear Thinking", "Books", "A practical guide to better decision-making.", Decimal("16.99"), "BK-ACT-PB", {"format": "Paperback"}, 80),
        ]

        created_count = 0
        for name, cat_name, description, price, sku, attrs, stock in demo_products:
            slug = name.lower().replace(" ", "-").replace("’", "").replace("'", "")
            product, created = Product.all_objects.get_or_create(
                slug=slug,
                defaults=dict(
                    category=category_objs[cat_name], name=name, description=description,
                    status=Product.Status.ACTIVE, base_price=price,
                ),
            )
            if not created and product.is_deleted:
                product.restore()
                product.status = Product.Status.ACTIVE
                product.save(update_fields=["status"])
            elif not created and product.status != Product.Status.ACTIVE:
                product.status = Product.Status.ACTIVE
                product.save(update_fields=["status"])
            if created:
                ProductVariant.objects.create(product=product, sku=sku, attributes=attrs, stock_quantity=stock)
                ProductSellerAssignment.objects.create(
                    product=product, seller=seller, role=ProductSellerAssignment.Role.PRIMARY_SELLER, price=price
                )
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f"Created {created_count} demo products across {len(categories)} categories."))
        self.stdout.write(self.style.SUCCESS("Seed complete."))
