from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from catalog.models import Category, Product, Review
from content.models import Article


IMG = {
    "women": "https://images.unsplash.com/photo-1556228578-0d85b1a4d571?w=900&q=80",
    "oils": "https://images.unsplash.com/photo-1608571423902-eed4a5ad8108?w=900&q=80",
    "eye": "https://images.unsplash.com/photo-1587854692152-cbe660dbde88?w=900&q=80",
    "skin": "https://images.unsplash.com/photo-1570172616994-4597c4d6433d?w=900&q=80",
    "cream": "https://images.unsplash.com/photo-1608248543803-ba4f8c70ae0b?w=900&q=80",
    "soap": "https://images.unsplash.com/photo-1617897903246-719242758050?w=900&q=80",
    "serum": "https://images.unsplash.com/photo-1620916566398-39f1143ab7be?w=900&q=80",
    "tea": "https://images.unsplash.com/photo-1597318181409-cf64d0b5d8a2?w=900&q=80",
}


ADMIN_USERNAME = "admin"
ADMIN_EMAIL = "info@jakeala.com"
ADMIN_PASSWORD = "jakeala2026"


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
            ("Women's Wellness", "womens-wellness", "Everyday rituals for feminine balance", "Thoughtful herbal support for cycle comfort, energy and inner calm.", IMG["women"], 1),
            ("Essential Oils", "essential-oils", "Botanical aromas, purposeful blends", "Steam-distilled oils and blends for atmosphere, massage and self-care.", IMG["oils"], 2),
            ("Eye Health", "eye-health", "Nourish vision from the inside", "Supplements formulated with lutein, zeaxanthin and botanical antioxidants.", IMG["eye"], 3),
            ("Skin & Body", "skin-body", "Clean textures the skin understands", "Handcrafted creams, oils and washes with transparent botanical inputs.", IMG["skin"], 4),
        ]
        cat_map = {}
        for name, slug, tag, desc, img, order in cats:
            c, _ = Category.objects.update_or_create(
                slug=slug,
                defaults={"name": name, "tagline": tag, "description": desc, "image": img, "sort_order": order},
            )
            cat_map[slug] = c

        products = [
            dict(
                category=cat_map["skin-body"],
                name="Shea & Hibiscus Body Butter",
                slug="shea-hibiscus-body-butter",
                short_benefit="Deep moisture with a petal-soft finish.",
                description="Whipped West African shea and hibiscus extract melt into dry skin, leaving a cushioned glow without a heavy film.",
                price="8500.00",
                compare_at="9800.00",
                size="250 ml",
                sku="JN-SB-001",
                image=IMG["cream"],
                gallery=[IMG["cream"], IMG["skin"], IMG["soap"]],
                benefits=["Locks in moisture for 24 hours", "Calms tightness after bathing", "Subtle hibiscus-vanilla scent"],
                ingredients="Butyrospermum Parkii (Shea) Butter, Cocos Nucifera Oil, Hibiscus Sabdariffa Extract, Tocopherol, Cera Alba, Vanilla Planifolia.",
                directions="Warm a pearl-size amount between palms. Sweep over damp skin after bathing.",
                who_it_is_for="Dry, mature and sensitive skin seeking richer moisture.",
                warnings="For external use only. Patch test on inner arm. Discontinue if irritation occurs.",
                disclaimer="",
                faqs=[{"q": "Is it greasy?", "a": "It absorbs in under a minute on damp skin."}, {"q": "Is it scented?", "a": "A soft botanical vanilla-hibiscus, no synthetic perfume."}],
                is_featured=True,
                is_supplement=False,
                rating="4.90",
                review_count=128,
            ),
            dict(
                category=cat_map["skin-body"],
                name="Turmeric Glow Cleansing Bar",
                slug="turmeric-glow-cleansing-bar",
                short_benefit="Gentle daily cleanse with golden botanicals.",
                description="Cold-process soap with turmeric, honey and oat to lift dullness without stripping the barrier.",
                price="3200.00",
                size="120 g",
                sku="JN-SB-002",
                image=IMG["soap"],
                gallery=[IMG["soap"]],
                benefits=["Brightens uneven tone over time", "Oat soothes tightness", "Honey humectant finish"],
                ingredients="Sodium Olivate, Sodium Cocoate, Aqua, Curcuma Longa Root Powder, Mel, Avena Sativa Kernel Flour.",
                directions="Work into a cream lather. Massage 30 seconds. Rinse.",
                who_it_is_for="Combination and dull-looking skin.",
                warnings="Turmeric may temporarily tint very fair fabrics. Patch test recommended.",
                faqs=[{"q": "Will it stain my washcloth?", "a": "Rinse promptly; staining is uncommon on modern fabrics."}],
                is_featured=True,
                rating="4.70",
                review_count=86,
            ),
            dict(
                category=cat_map["skin-body"],
                name="Rosehip Restore Face Serum",
                slug="rosehip-restore-face-serum",
                short_benefit="Lightweight oil serum for texture and glow.",
                description="Cold-pressed rosehip and squalane support the look of fine lines and post-blemish marks.",
                price="12500.00",
                size="30 ml",
                sku="JN-SB-003",
                image=IMG["serum"],
                gallery=[IMG["serum"]],
                benefits=["Softens the look of texture", "Non-comedogenic oil profile", "Evening ritual staple"],
                ingredients="Rosa Canina Fruit Oil, Squalane, Tocopherol, Calendula Officinalis Extract.",
                directions="2–3 drops after water-based serums, night or morning.",
                who_it_is_for="Normal, dry and combination skin.",
                warnings="Introduce slowly if you are oil-averse. Discontinue if breakouts persist.",
                faqs=[{"q": "Can I use with retinoids?", "a": "Yes — apply after water-based actives, before cream."}],
                is_featured=True,
                rating="4.85",
                review_count=64,
            ),
            dict(
                category=cat_map["essential-oils"],
                name="Calm Grove Essential Blend",
                slug="calm-grove-essential-blend",
                short_benefit="Cedar, lavender and sweet orange for evening air.",
                description="A grounding diffusion blend designed for wind-down rituals and quiet rooms.",
                price="7800.00",
                size="15 ml",
                sku="JN-EO-001",
                image=IMG["oils"],
                gallery=[IMG["oils"]],
                benefits=["Softens the atmosphere", "Pairs with massage oil", "No synthetic fragrance"],
                ingredients="Lavandula Angustifolia Oil, Cedrus Atlantica Oil, Citrus Sinensis Peel Oil.",
                directions="3–5 drops in a water diffuser. For massage, dilute to 1% in a carrier oil.",
                who_it_is_for="Anyone building a calmer evening ritual.",
                warnings="Never ingest. Keep away from eyes and children. Dilute before skin use. Not for use in pregnancy without practitioner advice.",
                faqs=[{"q": "Safe around pets?", "a": "Diffuse in a ventilated room and allow pets an exit path."}],
                is_featured=True,
                rating="4.80",
                review_count=51,
            ),
            dict(
                category=cat_map["essential-oils"],
                name="Citrus Dawn Single-Note Orange",
                slug="citrus-dawn-orange-oil",
                short_benefit="Bright steam-distilled sweet orange.",
                description="A single-note oil for morning diffusion and homemade cleaning sprays.",
                price="4500.00",
                size="15 ml",
                sku="JN-EO-002",
                image=IMG["oils"],
                gallery=[IMG["oils"]],
                benefits=["Uplifting citrus aroma", "Versatile household use when diluted"],
                ingredients="Citrus Sinensis Peel Oil.",
                directions="Diffuse 4 drops. Phototoxic — do not apply neat before sun exposure.",
                who_it_is_for="Homes that love a clean, bright scent.",
                warnings="Phototoxic. Dilute. External use only.",
                faqs=[],
                is_featured=False,
                rating="4.60",
                review_count=33,
            ),
            dict(
                category=cat_map["womens-wellness"],
                name="Moon Cycle Comfort Tea",
                slug="moon-cycle-comfort-tea",
                short_benefit="A warming cup for cramp-heavy days.",
                description="Ginger, raspberry leaf and chamomile blended for comfort-led evenings.",
                price="6200.00",
                size="40 g / 20 sachets",
                sku="JN-WW-001",
                image=IMG["tea"],
                gallery=[IMG["tea"], IMG["women"]],
                benefits=["Soothing warm ritual", "Caffeine-free", "Gently spiced"],
                ingredients="Zingiber Officinale, Rubus Idaeus Leaf, Matricaria Recutita, Cinnamomum Verum.",
                directions="Steep 1 sachet in 200 ml just-boiled water for 6 minutes.",
                who_it_is_for="Women seeking a comforting herbal cup around their cycle.",
                warnings="Not a medicine. Consult a clinician if pregnant or on medication.",
                disclaimer="This product is not intended to diagnose, treat, cure or prevent any disease.",
                faqs=[{"q": "How often?", "a": "1–2 cups on days you want extra comfort."}],
                is_featured=True,
                rating="4.75",
                review_count=90,
            ),
            dict(
                category=cat_map["womens-wellness"],
                name="Balance Oil Roller",
                slug="balance-oil-roller",
                short_benefit="Pulse-point blend for mid-day reset.",
                description="Clary sage and geranium in jojoba, sized for a bag or desk drawer.",
                price="5400.00",
                size="10 ml roller",
                sku="JN-WW-002",
                image=IMG["oils"],
                gallery=[IMG["oils"]],
                benefits=["Portable ritual", "Pre-diluted for skin"],
                ingredients="Simmondsia Chinensis Oil, Salvia Sclarea Oil, Pelargonium Graveolens Oil.",
                directions="Roll onto wrists and breathe slowly for four counts.",
                who_it_is_for="On-the-go wellness routines.",
                warnings="Avoid broken skin. External use only.",
                faqs=[],
                is_featured=False,
                rating="4.55",
                review_count=27,
            ),
            dict(
                category=cat_map["eye-health"],
                name="Lutein + Berry Vision Capsules",
                slug="lutein-berry-vision-capsules",
                short_benefit="Daily lutein, zeaxanthin and bilberry.",
                description="A science-aware supplement for adults who spend long hours on screens.",
                price="18900.00",
                size="60 capsules / 30 days",
                sku="JN-EH-001",
                image=IMG["eye"],
                gallery=[IMG["eye"]],
                benefits=["Provides lutein and zeaxanthin", "Includes bilberry extract", "Once-daily adult serving"],
                ingredients="Lutein, Zeaxanthin, Vaccinium Myrtillus Extract, Sunflower Oil, Vegetarian Capsule.",
                directions="Adults: 2 capsules daily with food.",
                who_it_is_for="Adults seeking nutritional support for eye health.",
                warnings="Keep out of reach of children. Do not exceed the stated dose. Seek advice if pregnant, nursing or on medication.",
                disclaimer="These statements have not been evaluated by the FDA or NAFDAC. This product is not intended to diagnose, treat, cure or prevent any disease.",
                faqs=[{"q": "Can I take with other vitamins?", "a": "Usually yes — ask your clinician about total lutein intake."}],
                is_featured=True,
                is_supplement=True,
                rating="4.65",
                review_count=41,
            ),
        ]

        for data in products:
            slug = data["slug"]
            Product.objects.update_or_create(slug=slug, defaults=data)

        p = Product.objects.get(slug="shea-hibiscus-body-butter")
        Review.objects.get_or_create(
            product=p, author="Amaka O.",
            defaults={"rating": 5, "title": "Finally a butter that sinks in", "body": "My elbows and shins stay soft through harmattan. The scent is quiet and lovely."},
        )
        Review.objects.get_or_create(
            product=p, author="Chioma E.",
            defaults={"rating": 5, "title": "Gifted and kept one", "body": "Texture is cloud-like. Using after evening shower has become a ritual."},
        )

        articles = [
            ("How to read a botanical INCI list", "reading-inci-lists", "A calm walkthrough of ingredient order, extracts and what 'fragrance' can hide.", "Ingredient Guides",
             "The first five ingredients usually make up most of the formula. Look for butters and oils you recognise. Extracts appear lower because they are used in smaller amounts. Jakeala lists every botanical input in plain language on every product page."),
            ("Building a 5-minute evening ritual", "five-minute-evening-ritual", "Oil, breath, and a warm cloth — no 12-step performance required.", "Self-Care",
             "Dim one light. Cleanse. Press a facial oil into damp skin. Sit for four slow breaths. That is enough on a difficult day. Consistency outruns complexity."),
            ("Screen hours and nutritional support", "screen-hours-nutrition", "What lutein and zeaxanthin actually do — and what a supplement cannot claim.", "Eye Health",
             "Macular pigments help filter high-energy visible light. A supplement can contribute to daily intake. It is not a treatment for eye disease. Rest your gaze every 20 minutes and keep check-ups with an optometrist."),
        ]
        for title, slug, excerpt, label, body in articles:
            Article.objects.update_or_create(
                slug=slug,
                defaults={"title": title, "excerpt": excerpt, "body": body, "category_label": label, "cover": IMG["skin"]},
            )

        self.stdout.write(self.style.SUCCESS("Seeded Jakeala Naturals catalog, reviews and articles."))
