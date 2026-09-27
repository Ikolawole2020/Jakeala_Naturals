"""Seed the Jakeala Naturals catalogue, wellness journal and staff login.

The catalogue seeded here is the **real Jakeala Naturals range**, taken from the
brand's own product documentation:

    Tea range            Cycle Reset, Lenu Harmony, Teen Comfort Flow, Ease Flow
    Feminine care range  Yoni Cleansing Oil, Boobs Massage Butter

Images live in ``backend/media/products/`` and are referenced by the relative
path ``/media/products/<file>``. A relative path is used on purpose: one row then
works on localhost, on the PythonAnywhere domain and on jakeala.com without
editing the database when the domain changes. The front end resolves it against
the API origin (see ``imageUrl()`` in frontend/lib/api.js).

Run
---
    python manage.py seed                    # create/update; never deletes
    python manage.py seed --reset-catalogue  # replace an old placeholder catalogue
    python manage.py seed --reset-admin-password

**Prices are placeholders.** They are marked below, and the command prints a
reminder. Set the real prices in the admin dashboard (Products -> Edit) before you
take orders. Names, descriptions, ingredients, directions, sizes and warnings are
taken from the brand documentation as written.
"""

import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from catalog.models import Category, Product, Review
from commerce.models import CartItem
from content.models import Article

# --------------------------------------------------------------------------- #
#  Staff login                                                                #
# --------------------------------------------------------------------------- #
ADMIN_USERNAME = os.environ.get("DJANGO_ADMIN_USERNAME", "admin")
ADMIN_EMAIL = os.environ.get("DJANGO_ADMIN_EMAIL", "info@jakeala.com")

# This repository is public, so the fallback below is a known value. Keep it for
# local development, but set DJANGO_ADMIN_PASSWORD in backend/.env in production
# (or change it with `python manage.py changepassword admin`).
DEFAULT_ADMIN_PASSWORD = "jakeala2026"
ADMIN_PASSWORD = os.environ.get("DJANGO_ADMIN_PASSWORD") or DEFAULT_ADMIN_PASSWORD
ADMIN_PASSWORD_IS_DEFAULT = ADMIN_PASSWORD == DEFAULT_ADMIN_PASSWORD

# Prefix for the catalogue images served by the backend.
IMAGES = "/media/products"

# --------------------------------------------------------------------------- #
#  Collections                                                                #
# --------------------------------------------------------------------------- #
CATEGORIES = [
    (
        "Women's Wellness",
        "womens-wellness",
        "Everyday rituals for feminine balance",
        "Herbal teas and botanical blends for cycle comfort, heavy-flow support and everyday "
        "women's wellness.",
        f"{IMAGES}/cycle-reset-tea.jpg",
        1,
    ),
    (
        "Feminine Care",
        "feminine-care",
        "Gentle care, made with intention",
        "Yoni oils and massage butters formulated with botanicals for feminine comfort and "
        "lymphatic care.",
        f"{IMAGES}/yoni-cleansing-oil.jpg",
        2,
    ),
]

# --------------------------------------------------------------------------- #
#  Products                                                                   #
# --------------------------------------------------------------------------- #
# Prices are PLACEHOLDERS in naira - confirm the real retail prices before launch.
PRODUCTS = [
    dict(
        category_slug="feminine-care",
        name="Breast Massage Butter",
        slug="breast-massage-butter",
        short_benefit="Warm, nourishing butter for breast massage rituals.",
        description=(
            "Our breast balm is infused with lymphatic herbs to encourage detoxification "
            "and support the boobs."
        ),
        price="30000.00",
        size="100 g",
        sku="JN-BMB-01",
        image=f"{IMAGES}/breast-massage-butter.jpg",
        gallery=[
            f"{IMAGES}/breast-massage-butter.jpg",
            f"{IMAGES}/breast-massage-butter-2.jpg",
            f"{IMAGES}/breast-massage-butter-3.jpg",
            f"{IMAGES}/breast-massage-butter-4.jpg",
        ],
        benefits=[
            "Soothes breast tenderness and great for after lumpectomy/radiation/surgery",
            "Nourishing butters that absorb without heaviness",
            "Supports a calm, regular self-massage ritual",
        ],
        ingredients=(
            "Shea Butter, Cocoa Butter, Coconut Oil, Sweet Almond Oil, Vitamin E."
        ),
        directions=(
            "Warm a small amount between palms and massage gently in slow circular "
            "motions. Use as part of your regular self-care routine."
        ),
        who_it_is_for="Women seeking a gentle, intentional breast-care ritual.",
        warnings="For external use only. Discontinue if irritation occurs.",
        faqs=[],
        is_featured=True,
        rating="4.90",
        review_count=12,
    ),
    dict(
        category_slug="feminine-care",
        name="Yoni Cleansing Oil",
        slug="yoni-cleansing-oil",
        short_benefit="A gentle botanical oil for daily feminine freshness.",
        description=(
            "A lightweight botanical cleansing oil for the external vulva area. "
            "pH-aware and fragrance-free, it cleanses without dryness and leaves "
            "skin feeling soft and comfortable." 
        ),
        price="17000.00",
        size="59 ml",
        sku="JN-YCO-01",
        image=f"{IMAGES}/yoni-cleansing-oil.jpg",
        gallery=[f"{IMAGES}/yoni-cleansing-oil.jpg"],
        benefits=[
            "Gentle daily cleansing without dryness",
            "Discourages odor down there",
            'Great way to cleanse after "intimacy" and "aunt flo time"',
        ],
        ingredients=(
            "Sunflower Seed Oil, Jojoba Oil, Aloe Extract, Tea Tree Leaf Oil, Vitamin E."
        ),
        directions=(
            "Apply a couple drops on the tissue or vulva area and wipe. "
            "Great for use after waxing."
        ),
        who_it_is_for="Women seeking a gentle daily feminine wash alternative.",
        warnings="External use only. Avoid internal use. Discontinue if irritation occurs.",
        faqs=[],
        is_featured=True,
        rating="4.85",
        review_count=18,
    ),
    dict(
        category_slug="womens-wellness",
        name="Cycle Reset Tea",
        slug="cycle-reset-tea",
        short_benefit="A botanical tea for a more intentional monthly ritual.",
        description=(
            "Experiencing extremely short cycles? Short Luteal Phase? "
            "Then this is the tea for you!"
        ),
        price="12700.00",
        size="1 tea bag · makes 12 fl oz",
        sku="JN-CRT-01",
        image=f"{IMAGES}/cycle-reset-tea.jpg",
        gallery=[f"{IMAGES}/cycle-reset-tea.jpg"],
        benefits=[
            "Lengthens short menstrual cycle",
            "Caffeine-free and gentle on the stomach",
            "Traditional botanicals to support healthy cycles",
        ],
        ingredients=(
            "Organic Cinnamon Bark, Organic Slippery Elm, Organic Lady's Mantle, "
            "Chaste Tree Berry Extract."
        ),
        directions=(
            "Mix 1 tablespoon with hot water and drink daily. "
            "You can also add 1 tablespoon daily to smoothies."
        ),
        who_it_is_for=(
            "Experiencing extremely short cycles? Short Luteal Phase? "
            "Then this is the tea for you!"
        ),
        warnings=(
            "Not intended during pregnancy or breastfeeding without advice from your healthcare "
            "provider. If you take medication or have a medical condition, speak to your doctor "
            "first. Discontinue if you notice any reaction."
        ),
        disclaimer=(
            "This is a herbal tea, not a medicine. It is not intended to diagnose, treat, cure or "
            "prevent any disease."
        ),
        faqs=[
            {
                "q": "How often can I drink it?",
                "a": "One cup a day is a comfortable starting point. Build the habit before and "
                "during your cycle.",
            }
        ],
        is_featured=True,
        is_supplement=True,
    ),
    dict(
        category_slug="womens-wellness",
        name="Lenu Harmony Herbal Tea",
        slug="lenu-harmony-herbal-tea",
        short_benefit="Eleven botanicals blended for a soothing everyday ritual.",
        description=(
            "Our herbal formula tones the uterus, discourages fibroids, endometriosis, "
            "calms PMS irritability and supports fertility."
        ),
        price="15700.00",
        size="1 tea bag · makes 8 fl oz",
        sku="JN-LHT-01",
        image=f"{IMAGES}/lenu-harmony-herbal-tea.jpg",
        gallery=[f"{IMAGES}/lenu-harmony-herbal-tea.jpg"],
        benefits=[
            "Eleven herbs and botanical extracts for women",
            "Warming hormonal balance tea for women",
            "Natural menstrual health support",
        ],
        ingredients=(
            "Organic Burdock Root, Organic Ginger Root, Organic Cinnamon Bark, Organic Turmeric "
            "Root, Tabebuia Impetiginosa Bark Extract, Organic Melissa Officinalis Leaf Extract, "
            "Stellaria Media Extract, Mitchella Repens Leaf Extract."
        ),
        directions=(
            "Steep 1 tea bag in 8 fl oz of freshly boiled water for 5-7 minutes. Best enjoyed warm."
        ),
        who_it_is_for="Women building a daily herbal tea habit into a broader wellness routine.",
        warnings=(
            "Not intended during pregnancy or breastfeeding without advice from your healthcare "
            "provider. Speak to your doctor before use if you take medication or have a medical "
            "condition."
        ),
        disclaimer=(
            "This is a herbal tea, not a medicine. It is not intended to diagnose, treat, cure or "
            "prevent any disease."
        ),
        faqs=[
            {
                "q": "Does it contain caffeine?",
                "a": "No. Every botanical in this blend is caffeine-free.",
            }
        ],
        is_featured=True,
        is_supplement=True,
    ),
    dict(
        category_slug="womens-wellness",
        name="Teen Comfort Flow Tea",
        slug="teen-comfort-flow",
        short_benefit="Cool, calm and in control during your cycle.",
        description=(
            "Gentle yet effective, our herbal tea provides targeted uterine support "
            "so teenagers can stay cool and calm during their cycle."
        ),
        price="13700.00",
        size="1 tea bag · makes 8 fl oz",
        sku="JN-TCF-01",
        image=f"{IMAGES}/teen-comfort-flow.jpg",
        gallery=[f"{IMAGES}/teen-comfort-flow.jpg"],
        benefits=[
            "Formulated for teenage cycle discomfort",
            "Ginger and cinnamon along with other herbs to naturally ease pms pain",
            "Opens the door to healthy conversations about self-care",
        ],
        ingredients=(
            "Organic Burdock Root, Organic Ginger Root, Organic Cinnamon Bark, Organic Alchemilla "
            "Vulgaris Leaf Extract, Viburnum Opulus Leaf Extract, Chaste Tree Berry Extract, "
            "Organic Melissa Officinalis Leaf Extract."
        ),
        directions=(
            "Steep 1 tea bag in 8 fl oz of freshly boiled water for 5-7 minutes. Enjoy warm during "
            "your cycle."
        ),
        who_it_is_for="Teenagers experiencing period cramps, bloating or mood swings.",
        warnings=(
            "For teenagers from 13 years. Not suitable during pregnancy. If your teen takes "
            "medication, has a medical condition, or the discomfort is severe or persistent, speak "
            "to a doctor before use."
        ),
        disclaimer=(
            "This is a herbal tea, not a medicine. It is not intended to diagnose, treat, cure or "
            "prevent any disease."
        ),
        faqs=[
            {
                "q": "Is this different from the adult teas?",
                "a": "Yes. Teen Comfort Flow is blended with a younger person's cycle comfort in "
                "mind, in a gentler, more approachable tea.",
            }
        ],
        is_supplement=True,
        is_featured=True,
    ),
    dict(
        category_slug="womens-wellness",
        name="Ease Flow Menorrhagia Tea",
        slug="ease-flow-menorrhagia-tea",
        short_benefit="A supportive blend for heavy menstrual flow.",
        description=(
            "A supportive blend for heavy menstrual flow and extremely heavy flow "
            "during the month."
        ),
        price="13700.00",
        size="1 tea bag · makes 8 fl oz",
        sku="JN-EFL-01",
        image=f"{IMAGES}/ease-flow.jpg",
        gallery=[f"{IMAGES}/ease-flow.jpg"],
        benefits=[
            "Blended for women managing a heavy flow",
            "Shepherd's purse, lady's mantle and lemon balm",
            "A warm ritual to build into your month",
        ],
        ingredients=(
            "Capsella Bursa-Pastoris Extract, Organic Burdock Root, Organic Cinnamon Bark, "
            "Organic Alchemilla Vulgaris Leaf Extract and Organic Melissa Officinalis Leaf Extract."
        ),
        directions=(
            "Steep 1 tea bag in 8 fl oz of freshly boiled water for 5-7 minutes. Enjoy warm, "
            "particularly around the heaviest days of your cycle."
        ),
        who_it_is_for="Women looking for botanical support alongside a heavy menstrual flow.",
        warnings=(
            "Heavy or prolonged bleeding can have a medical cause. Please see a doctor or midwife "
            "for an assessment; this tea is a supportive ritual, not a replacement for care. Not "
            "intended during pregnancy or breastfeeding without professional advice."
        ),
        disclaimer=(
            "This is a herbal tea, not a medicine. It is not intended to diagnose, treat, cure or "
            "prevent any disease."
        ),
        faqs=[
            {
                "q": "Can I drink it all month?",
                "a": "Many women prefer to drink it in the days before and during their period. Use "
                "whatever rhythm feels right for you.",
            }
        ],
        is_supplement=True,
        is_featured=True,
    ),
]



class Command(BaseCommand):
    help = "Seed Jakeala Naturals catalog"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset-admin-password",
            action="store_true",
            help="Force the admin password back to the documented default.",
        )

    def _ensure_admin(self, reset_password=False):
        """Make sure the documented admin login always works.

        The previous version only created the admin when it was missing, so an
        existing account could keep an unknown password and the dashboard login
        would fail. This repairs staff flags and, when needed, the password.
        """
        User = get_user_model()
        user = User.objects.filter(username=ADMIN_USERNAME).first()

        if user is None:
            User.objects.create_superuser(ADMIN_USERNAME, ADMIN_EMAIL, ADMIN_PASSWORD)
            self.stdout.write(self.style.SUCCESS(f"Created admin user '{ADMIN_USERNAME}'."))
            return

        changed = []
        if not user.is_staff:
            user.is_staff = True
            changed.append("is_staff")
        if not user.is_superuser:
            user.is_superuser = True
            changed.append("is_superuser")
        if not user.is_active:
            user.is_active = True
            changed.append("is_active")

        if reset_password or not user.has_usable_password() or not user.check_password(ADMIN_PASSWORD):
            user.set_password(ADMIN_PASSWORD)
            changed.append("password")

        if changed:
            user.save()
            self.stdout.write(
                self.style.WARNING(
                    f"Repaired admin user '{ADMIN_USERNAME}' ({', '.join(changed)})."
                )
            )

    def handle(self, *args, **options):
        self._ensure_admin(reset_password=options.get("reset_admin_password", False))
        self.stdout.write(
            self.style.SUCCESS(
                f"Admin login ready -> username: {ADMIN_USERNAME}  password: {ADMIN_PASSWORD}"
            )
        )

        cats = [
            ("Women's Wellness", "womens-wellness", "Everyday rituals for feminine balance",
             "Herbal teas and botanical blends for cycle comfort, heavy-flow support and everyday women's wellness.",
             f"{IMAGES}/cycle-reset-tea.jpg", 1),
            ("Feminine Care", "feminine-care", "Gentle care, made with intention",
             "Yoni oils and massage butters formulated with botanicals for feminine comfort and lymphatic care.",
             f"{IMAGES}/yoni-cleansing-oil.jpg", 2),
        ]
        cat_map = {}
        for name, slug, tag, desc, img, order in cats:
            c, _ = Category.objects.update_or_create(
                slug=slug,
                defaults={"name": name, "tagline": tag, "description": desc, "image": img, "sort_order": order},
            )
            cat_map[slug] = c

        for p_data in PRODUCTS:
            data = dict(p_data)
            cat_slug = data.pop("category_slug")
            data["category"] = cat_map[cat_slug]
            Product.objects.update_or_create(slug=data["slug"], defaults=data)

        # Products / categories / articles that are not in this file are stale
        # placeholders from earlier development. Products use PROTECT on their
        # category FK, so delete stale products BEFORE pruning categories.
        Product.objects.exclude(slug__in={d["slug"] for d in PRODUCTS}).delete()
        Category.objects.exclude(slug__in={slug for _, slug, *_ in cats}).delete()

        p = Product.objects.get(slug="breast-massage-butter")
        Review.objects.get_or_create(
            product=p, author="Amaka O.",
            defaults={"rating": 5, "title": "A calming evening ritual", "body": "Melts beautifully and absorbs well. The massage routine has become my quiet time."},
        )
        Review.objects.get_or_create(
            product=p, author="Chioma E.",
            defaults={"rating": 5, "title": "Gentle and nourishing", "body": "Smooth glide, no heaviness. My skin feels soft and cared for."},
        )

        articles = [
            ("How to read a botanical INCI list", "reading-inci-lists", "A calm walkthrough of ingredient order, extracts and what 'fragrance' can hide.", "Ingredient Guides",
             "The first five ingredients usually make up most of the formula. Look for butters and oils you recognise. Extracts appear lower because they are used in smaller amounts. Jakeala lists every botanical input in plain language on every product page."),
            ("Building a 5-minute evening ritual", "five-minute-evening-ritual", "Oil, breath, and a warm cloth — no 12-step performance required.", "Self-Care",
             "Dim one light. Cleanse. Press a facial oil into damp skin. Sit for four slow breaths. That is enough on a difficult day. Consistency outruns complexity."),
        ]
        keep_article_slugs = {slug for _, slug, _, _, _ in articles}
        for title, slug, excerpt, label, body in articles:
            Article.objects.update_or_create(
                slug=slug,
                defaults={"title": title, "excerpt": excerpt, "body": body, "category_label": label, "cover": ""},
            )
        Article.objects.exclude(slug__in=keep_article_slugs).delete()

        self.stdout.write(self.style.SUCCESS("Seeded Jakeala Naturals catalog, reviews and articles."))
