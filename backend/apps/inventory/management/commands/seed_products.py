"""
Management command: seed_products

Creates ~20 realistic Upstream Literacy products with categories, skill tags,
SKUs, and stock levels. Safe to run multiple times (uses get_or_create throughout).

Usage:
    python manage.py seed_products
    python manage.py seed_products --clear   # drops existing seed data first
"""

import random

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from apps.catalog.models import (
    BundleComponent,
    Category,
    Product,
    ProductCategory,
    ProductImage,
    SKU,
    SkillTag,
)
from apps.checkout.models import ShippingRate
from apps.inventory.models import StockLevel, StockMovement


# ---------------------------------------------------------------------------
# Seed data definitions
# ---------------------------------------------------------------------------

GRADE_CATEGORIES = [
    {"name": "Pre-K", "slug": "pre-k", "display_order": 10},
    {"name": "Kindergarten", "slug": "kindergarten", "display_order": 20},
    {"name": "Grade 1", "slug": "grade-1", "display_order": 30},
    {"name": "Grade 2", "slug": "grade-2", "display_order": 40},
    {"name": "Grade 3", "slug": "grade-3", "display_order": 50},
    {"name": "Grade 4", "slug": "grade-4", "display_order": 60},
    {"name": "Grade 5", "slug": "grade-5", "display_order": 70},
]

FOCUS_CATEGORIES = [
    {"name": "Phonics", "slug": "phonics", "display_order": 10},
    {"name": "Phonemic Awareness", "slug": "phonemic-awareness", "display_order": 20},
    {"name": "Fluency", "slug": "fluency", "display_order": 30},
    {"name": "Vocabulary", "slug": "vocabulary", "display_order": 40},
    {"name": "Comprehension", "slug": "comprehension", "display_order": 50},
]

FORMAT_CATEGORIES = [
    {"name": "Decodable Readers", "slug": "decodable-readers", "display_order": 10},
    {"name": "Teacher Guides", "slug": "teacher-guides", "display_order": 20},
    {"name": "Student Workbooks", "slug": "student-workbooks", "display_order": 30},
    {"name": "Kits & Bundles", "slug": "kits-bundles", "display_order": 40},
    {"name": "Digital Downloads", "slug": "digital-downloads", "display_order": 50},
]

PARENT_CATEGORIES = [
    {"name": "By Grade", "slug": "by-grade", "display_order": 10},
    {"name": "By Focus", "slug": "by-focus", "display_order": 20},
    {"name": "By Format", "slug": "by-format", "display_order": 30},
]

SKILL_TAGS = [
    {"name": "CVC Words", "slug": "cvc-words", "curriculum_standard": "RF.K.3"},
    {"name": "Blending", "slug": "blending", "curriculum_standard": "RF.K.2"},
    {"name": "Segmenting", "slug": "segmenting", "curriculum_standard": "RF.K.2"},
    {"name": "Sight Words", "slug": "sight-words", "curriculum_standard": "RF.K.3c"},
    {"name": "Digraphs", "slug": "digraphs", "curriculum_standard": "RF.1.3"},
    {"name": "Vowel Teams", "slug": "vowel-teams", "curriculum_standard": "RF.2.3"},
    {"name": "R-Controlled Vowels", "slug": "r-controlled-vowels", "curriculum_standard": "RF.2.3"},
    {"name": "Long Vowels", "slug": "long-vowels", "curriculum_standard": "RF.1.3"},
    {"name": "Short Vowels", "slug": "short-vowels", "curriculum_standard": "RF.K.3"},
    {"name": "Fluency Building", "slug": "fluency-building", "curriculum_standard": "RF.1.4"},
    {"name": "Phoneme Manipulation", "slug": "phoneme-manipulation", "curriculum_standard": "RF.K.2"},
    {"name": "Word Families", "slug": "word-families", "curriculum_standard": "RF.K.3"},
    {"name": "Multisyllabic Words", "slug": "multisyllabic-words", "curriculum_standard": "RF.3.3"},
    {"name": "Comprehension Strategies", "slug": "comprehension-strategies", "curriculum_standard": "RI.3.1"},
    {"name": "Vocabulary Development", "slug": "vocabulary-development", "curriculum_standard": "L.2.4"},
]

# Product definitions: (title, product_type, base_price, short_desc, desc,
#  grade_slugs, focus_slugs, format_slug, skill_tag_slugs, sku_code, format_specs)
PRODUCT_DEFINITIONS = [
    {
        "title": "Decodable Readers Set A — CVC Words",
        "product_type": "physical",
        "base_price": "18.99",
        "short_description": "A set of 10 decodable readers focused on CVC word patterns for early readers.",
        "description": (
            "This set of 10 leveled decodable readers gives young students repeated practice "
            "with consonant-vowel-consonant (CVC) word patterns. Each book uses a controlled "
            "vocabulary so students can apply their phonics knowledge immediately. Aligned to "
            "the Science of Reading, these books support Tier 1 and Tier 2 small-group instruction. "
            "Includes a teacher tip card with discussion prompts and comprehension questions."
        ),
        "grades": ["kindergarten", "grade-1"],
        "focus": ["phonics"],
        "format": "decodable-readers",
        "skill_tags": ["cvc-words", "short-vowels", "blending"],
        "sku_code": "DR-SET-A-CVC",
        "format_specs": {"pages_per_book": 16, "book_count": 10, "reading_level": "A-B"},
        "is_featured": True,
    },
    {
        "title": "Decodable Readers Set B — Digraphs & Blends",
        "product_type": "physical",
        "base_price": "21.99",
        "short_description": "12 decodable readers covering digraphs (sh, ch, th, wh) and initial blends.",
        "description": (
            "Build on foundational CVC skills with this 12-book reader set targeting consonant "
            "digraphs and initial consonant blends. Stories are engaging and predictable, with "
            "high-frequency words introduced gradually. Perfect for Grade 1 readers who have "
            "mastered CVC words and are ready for the next step. Includes a decodable word list "
            "and fluency tracking sheet."
        ),
        "grades": ["grade-1"],
        "focus": ["phonics", "fluency"],
        "format": "decodable-readers",
        "skill_tags": ["digraphs", "blending", "fluency-building"],
        "sku_code": "DR-SET-B-DIG",
        "format_specs": {"pages_per_book": 20, "book_count": 12, "reading_level": "C-D"},
        "is_featured": False,
    },
    {
        "title": "Decodable Readers Set C — Vowel Teams",
        "product_type": "physical",
        "base_price": "24.99",
        "short_description": "10 decodable readers focusing on vowel team patterns (ai, ay, ee, ea, oa).",
        "description": (
            "This set targets the most common vowel team patterns encountered in Grade 2 reading. "
            "Each reader is carefully controlled so that only previously taught patterns appear. "
            "The connected text is meaningful and builds vocabulary while reinforcing decoding. "
            "Includes a scope and sequence chart and teacher guide insert."
        ),
        "grades": ["grade-2"],
        "focus": ["phonics"],
        "format": "decodable-readers",
        "skill_tags": ["vowel-teams", "long-vowels"],
        "sku_code": "DR-SET-C-VT",
        "format_specs": {"pages_per_book": 24, "book_count": 10, "reading_level": "E-F"},
        "is_featured": False,
    },
    {
        "title": "Phonics Teacher Guide — Grade 1",
        "product_type": "physical",
        "base_price": "34.99",
        "short_description": "Comprehensive explicit phonics instruction guide for Grade 1 teachers.",
        "description": (
            "A complete, lesson-by-lesson teacher guide covering the full Grade 1 phonics scope "
            "and sequence. Each lesson includes a warm-up routine, explicit instruction script, "
            "guided practice activities, and formative assessment checkpoints. Includes 180 "
            "daily lesson plans, word lists, decodable sentence activities, and reproducible "
            "student practice pages. Aligned to the Science of Reading and structured literacy "
            "frameworks."
        ),
        "grades": ["grade-1"],
        "focus": ["phonics"],
        "format": "teacher-guides",
        "skill_tags": ["cvc-words", "digraphs", "blending", "short-vowels", "long-vowels"],
        "sku_code": "TG-PHONICS-G1",
        "format_specs": {"pages": 320, "binding": "spiral", "reproducibles": True},
        "is_featured": True,
    },
    {
        "title": "Phonics Teacher Guide — Grade 2",
        "product_type": "physical",
        "base_price": "34.99",
        "short_description": "Explicit phonics instruction guide covering Grade 2 patterns and multisyllabic words.",
        "description": (
            "Designed for Grade 2 teachers, this guide extends phonics instruction into vowel "
            "teams, r-controlled vowels, and introductory multisyllabic word strategies. Each "
            "lesson includes an explicit model-guide-practice structure, decodable word reading "
            "lists, and connected text passages. Includes 180 daily lessons with built-in "
            "spiral review."
        ),
        "grades": ["grade-2"],
        "focus": ["phonics"],
        "format": "teacher-guides",
        "skill_tags": ["vowel-teams", "r-controlled-vowels", "multisyllabic-words"],
        "sku_code": "TG-PHONICS-G2",
        "format_specs": {"pages": 296, "binding": "spiral", "reproducibles": True},
        "is_featured": False,
    },
    {
        "title": "Phonemic Awareness Teacher Guide — Pre-K & Kindergarten",
        "product_type": "physical",
        "base_price": "29.99",
        "short_description": "Structured oral language activities to develop phonemic awareness in young learners.",
        "description": (
            "This guide provides 150+ structured phonemic awareness activities organized by "
            "skill: rhyming, alliteration, syllable counting, onset-rime blending, phoneme "
            "isolation, blending, and segmentation. Each activity includes teacher language, "
            "student responses, and differentiation suggestions. No materials required beyond "
            "the guide — all activities are oral and kinesthetic."
        ),
        "grades": ["pre-k", "kindergarten"],
        "focus": ["phonemic-awareness"],
        "format": "teacher-guides",
        "skill_tags": ["blending", "segmenting", "phoneme-manipulation"],
        "sku_code": "TG-PA-PREK-K",
        "format_specs": {"pages": 240, "binding": "perfect-bound", "reproducibles": False},
        "is_featured": False,
    },
    {
        "title": "Kindergarten Phonics Student Workbook",
        "product_type": "physical",
        "base_price": "8.99",
        "short_description": "Full-year student workbook for Kindergarten phonics aligned to grade-level scope.",
        "description": (
            "This consumable student workbook provides a full year of Kindergarten phonics practice. "
            "Activities progress from letter-sound correspondence through CVC words and basic sight "
            "words. Clean, uncluttered pages reduce cognitive load and focus student attention. "
            "Sold individually; classroom packs available."
        ),
        "grades": ["kindergarten"],
        "focus": ["phonics"],
        "format": "student-workbooks",
        "skill_tags": ["cvc-words", "short-vowels", "sight-words"],
        "sku_code": "WB-PHONICS-K",
        "format_specs": {"pages": 128, "binding": "saddle-stitch", "consumable": True},
        "is_featured": False,
    },
    {
        "title": "Grade 1 Phonics Student Workbook",
        "product_type": "physical",
        "base_price": "9.99",
        "short_description": "Consumable student workbook for Grade 1 phonics practice.",
        "description": (
            "Aligned to the Grade 1 Phonics Teacher Guide, this workbook provides independent and "
            "guided practice for each lesson. Includes word sorting activities, sentence writing "
            "with decodable words, and reading fluency passages. Sold individually."
        ),
        "grades": ["grade-1"],
        "focus": ["phonics"],
        "format": "student-workbooks",
        "skill_tags": ["digraphs", "blending", "word-families"],
        "sku_code": "WB-PHONICS-G1",
        "format_specs": {"pages": 144, "binding": "saddle-stitch", "consumable": True},
        "is_featured": False,
    },
    {
        "title": "Grade 2 Phonics Student Workbook",
        "product_type": "physical",
        "base_price": "9.99",
        "short_description": "Consumable workbook for Grade 2 phonics, covering vowel teams and r-controlled vowels.",
        "description": (
            "Aligned to the Grade 2 Phonics Teacher Guide, this workbook offers structured practice "
            "pages for vowel teams, r-controlled vowels, and multisyllabic word strategies. Each "
            "unit ends with a decodable passage for fluency practice."
        ),
        "grades": ["grade-2"],
        "focus": ["phonics"],
        "format": "student-workbooks",
        "skill_tags": ["vowel-teams", "r-controlled-vowels"],
        "sku_code": "WB-PHONICS-G2",
        "format_specs": {"pages": 152, "binding": "saddle-stitch", "consumable": True},
        "is_featured": False,
    },
    {
        "title": "Sight Words Flash Cards — Pre-K through Grade 2",
        "product_type": "physical",
        "base_price": "12.99",
        "short_description": "220 high-frequency sight word cards organized by Fry list levels.",
        "description": (
            "This set of 220 durable sight word flash cards covers the first four Fry word lists "
            "(words 1–220). Cards are color-coded by level for easy sorting. Each card features "
            "the word in large print on the front, with example sentences on the back. Includes "
            "a storage ring and activity guide."
        ),
        "grades": ["pre-k", "kindergarten", "grade-1", "grade-2"],
        "focus": ["phonics", "vocabulary"],
        "format": "student-workbooks",
        "skill_tags": ["sight-words"],
        "sku_code": "FLASH-SIGHT-220",
        "format_specs": {"card_count": 220, "card_size": "4x6 inches", "laminated": False},
        "is_featured": False,
    },
    {
        "title": "Fluency Passage Pack — Grade 1",
        "product_type": "physical",
        "base_price": "19.99",
        "short_description": "60 reproducible one-minute fluency passages leveled for Grade 1 readers.",
        "description": (
            "This reproducible passage pack provides 60 leveled one-minute reading passages "
            "for Grade 1 fluency practice. Passages are organized by reading level (A through G) "
            "and use controlled vocabulary tied to common phonics patterns. Includes a student "
            "progress tracking chart and WCPM scoring guide."
        ),
        "grades": ["grade-1"],
        "focus": ["fluency"],
        "format": "student-workbooks",
        "skill_tags": ["fluency-building"],
        "sku_code": "FP-FLUENCY-G1",
        "format_specs": {"passage_count": 60, "reproducible": True, "levels": "A-G"},
        "is_featured": False,
    },
    {
        "title": "Fluency Passage Pack — Grade 2",
        "product_type": "physical",
        "base_price": "19.99",
        "short_description": "60 reproducible one-minute fluency passages leveled for Grade 2 readers.",
        "description": (
            "Extending the Grade 1 pack, these 60 Grade 2 passages focus on vowel team and "
            "r-controlled vowel patterns in connected text. Includes DIBELS-aligned progress "
            "monitoring tools and teacher scoring sheets."
        ),
        "grades": ["grade-2"],
        "focus": ["fluency"],
        "format": "student-workbooks",
        "skill_tags": ["fluency-building", "vowel-teams"],
        "sku_code": "FP-FLUENCY-G2",
        "format_specs": {"passage_count": 60, "reproducible": True, "levels": "H-M"},
        "is_featured": False,
    },
    {
        "title": "Vocabulary Builder — Grade 3",
        "product_type": "physical",
        "base_price": "22.99",
        "short_description": "Explicit vocabulary instruction program with 30 weekly lessons for Grade 3.",
        "description": (
            "This 30-week vocabulary program teaches Tier 2 academic words through the "
            "Frayer model, semantic mapping, and word-rich discussion routines. Each week "
            "introduces 8 new words with direct instruction, multiple exposures in varied "
            "contexts, and a formative assessment. Includes student vocabulary journals and "
            "a teacher guide."
        ),
        "grades": ["grade-3"],
        "focus": ["vocabulary"],
        "format": "student-workbooks",
        "skill_tags": ["vocabulary-development"],
        "sku_code": "VOC-BUILDER-G3",
        "format_specs": {"weeks": 30, "words_per_week": 8, "includes_journal": True},
        "is_featured": False,
    },
    {
        "title": "Comprehension Strategy Toolkit — Grades 3–5",
        "product_type": "physical",
        "base_price": "39.99",
        "short_description": "Research-based comprehension strategy instruction kit for upper elementary.",
        "description": (
            "This toolkit provides explicit instruction in six core comprehension strategies: "
            "activating background knowledge, questioning, visualizing, inferring, "
            "synthesizing, and summarizing. Includes 48 lesson plans, anchor charts, graphic "
            "organizers, and read-aloud text excerpts. Suitable for Grades 3–5 whole-class "
            "and small-group instruction."
        ),
        "grades": ["grade-3", "grade-4", "grade-5"],
        "focus": ["comprehension"],
        "format": "teacher-guides",
        "skill_tags": ["comprehension-strategies", "vocabulary-development"],
        "sku_code": "COMP-TOOLKIT-35",
        "format_specs": {"lesson_count": 48, "includes_anchor_charts": True, "grades": "3-5"},
        "is_featured": True,
    },
    {
        "title": "Phonemic Awareness Activity Cards — Kindergarten",
        "product_type": "physical",
        "base_price": "16.99",
        "short_description": "80 activity cards for small-group phonemic awareness practice.",
        "description": (
            "This set of 80 durable activity cards provides hands-on phonemic awareness practice "
            "for Kindergarten small groups. Activities include sound sorting, blending chains, "
            "segmenting with chips, and onset-rime manipulation. Cards are color-coded by skill "
            "level and include teacher instruction on the back of each card."
        ),
        "grades": ["kindergarten"],
        "focus": ["phonemic-awareness"],
        "format": "student-workbooks",
        "skill_tags": ["blending", "segmenting", "phoneme-manipulation"],
        "sku_code": "PA-CARDS-K",
        "format_specs": {"card_count": 80, "laminated": True, "storage_box": True},
        "is_featured": False,
    },
    {
        "title": "Word Families Poster Set",
        "product_type": "physical",
        "base_price": "14.99",
        "short_description": "24 classroom anchor chart posters covering the most common word families.",
        "description": (
            "This set of 24 full-color, 18x24 inch classroom posters features the most common "
            "word families (-at, -an, -ap, -ig, -it, -in, -ot, -op, -og, -ug, -un, -ut, and more). "
            "Each poster presents the rime unit prominently with 8 example words and an illustration. "
            "Printed on heavy-weight matte paper."
        ),
        "grades": ["kindergarten", "grade-1"],
        "focus": ["phonics"],
        "format": "student-workbooks",
        "skill_tags": ["word-families", "cvc-words"],
        "sku_code": "POSTER-WFAM-24",
        "format_specs": {"poster_count": 24, "size": "18x24 inches", "paper_weight": "80lb"},
        "is_featured": False,
    },
    {
        "title": "Structured Literacy Scope & Sequence — Digital Download",
        "product_type": "digital",
        "base_price": "9.99",
        "short_description": "Printable K–5 scope and sequence chart aligned to the Science of Reading.",
        "description": (
            "This professionally designed PDF scope and sequence covers Kindergarten through "
            "Grade 5 phonics, phonemic awareness, fluency, vocabulary, and comprehension skills. "
            "Formatted as a one-page-per-grade summary and a full multi-page reference document. "
            "Delivered as a print-ready PDF immediately upon purchase."
        ),
        "grades": ["pre-k", "kindergarten", "grade-1", "grade-2", "grade-3", "grade-4", "grade-5"],
        "focus": ["phonics", "phonemic-awareness", "fluency", "vocabulary", "comprehension"],
        "format": "digital-downloads",
        "skill_tags": [],
        "sku_code": "DL-SCOPE-SEQ-K5",
        "format_specs": {"file_format": "PDF", "pages": 8, "print_ready": True},
        "is_featured": False,
    },
    {
        "title": "Phonics Warm-Up Routines — Digital Download",
        "product_type": "digital",
        "base_price": "14.99",
        "short_description": "45 slide decks for daily phonics warm-up routines, Grades K–2.",
        "description": (
            "Download 45 ready-to-use Google Slides and PowerPoint decks for phonics warm-up "
            "routines. Each 5-minute routine includes a sound-spelling review, blending drill, "
            "and word chain activity. Organized by skill sequence for Grades K–2. Fully editable "
            "so teachers can customize vocabulary and examples."
        ),
        "grades": ["kindergarten", "grade-1", "grade-2"],
        "focus": ["phonics"],
        "format": "digital-downloads",
        "skill_tags": ["blending", "cvc-words", "digraphs"],
        "sku_code": "DL-WARMUP-K2",
        "format_specs": {"file_format": "PPTX + Google Slides", "slide_decks": 45, "editable": True},
        "is_featured": False,
    },
    {
        "title": "Decodable Passages — Grades 2–3 Digital Pack",
        "product_type": "digital",
        "base_price": "19.99",
        "short_description": "80 printable decodable reading passages for Grades 2–3.",
        "description": (
            "This digital download includes 80 decodable passages targeting Grade 2–3 phonics "
            "patterns including vowel teams, r-controlled vowels, and multisyllabic words. "
            "Each passage comes with comprehension questions and a fluency timing chart. "
            "Delivered as a print-ready PDF."
        ),
        "grades": ["grade-2", "grade-3"],
        "focus": ["phonics", "fluency", "comprehension"],
        "format": "digital-downloads",
        "skill_tags": ["vowel-teams", "r-controlled-vowels", "fluency-building", "comprehension-strategies"],
        "sku_code": "DL-PASSAGES-23",
        "format_specs": {"file_format": "PDF", "passage_count": 80, "print_ready": True},
        "is_featured": False,
    },
    {
        "title": "Multisyllabic Word Decoding Guide — Grade 4",
        "product_type": "physical",
        "base_price": "27.99",
        "short_description": "Explicit instruction in syllabication strategies and morpheme analysis for Grade 4.",
        "description": (
            "This teacher guide covers six syllable types and four morpheme strategies to help "
            "Grade 4 students decode and spell multisyllabic words with confidence. Includes 90 "
            "lesson plans, student practice pages, and a decodable word bank of 500+ multisyllabic "
            "words sorted by pattern."
        ),
        "grades": ["grade-4"],
        "focus": ["phonics", "vocabulary"],
        "format": "teacher-guides",
        "skill_tags": ["multisyllabic-words", "vocabulary-development"],
        "sku_code": "TG-MULTI-G4",
        "format_specs": {"pages": 260, "binding": "spiral", "word_bank_count": 500},
        "is_featured": False,
    },
]

# The bundle product definition (created after individual products exist)
BUNDLE_DEFINITION = {
    "title": "Grade 1 Complete Literacy Classroom Kit",
    "product_type": "bundle",
    "base_price": "64.99",
    "short_description": "Everything a Grade 1 teacher needs: phonics guide, workbooks, and decodable readers.",
    "description": (
        "The Grade 1 Complete Literacy Classroom Kit bundles our three most essential Grade 1 "
        "resources into one discounted package. Includes the Phonics Teacher Guide (Grade 1), "
        "a class set of 25 Grade 1 Phonics Student Workbooks, and Decodable Readers Set B. "
        "Save over 20% compared to purchasing separately. Packaged in a labeled storage box."
    ),
    "grades": ["grade-1"],
    "focus": ["phonics", "fluency"],
    "format": "kits-bundles",
    "skill_tags": ["blending", "digraphs", "fluency-building"],
    "sku_code": "KIT-G1-LITERACY",
    "format_specs": {"includes_storage_box": True, "class_set_quantity": 25},
    "is_featured": True,
    "components": [
        {"sku_code": "TG-PHONICS-G1", "quantity": 1},
        {"sku_code": "WB-PHONICS-G1", "quantity": 25},
        {"sku_code": "DR-SET-B-DIG", "quantity": 1},
    ],
}


class Command(BaseCommand):
    help = "Seed the database with realistic Upstream Literacy catalog and inventory data."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete all existing seed products, categories, and skill tags before seeding.",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            self.stdout.write("Clearing existing seed data...")
            Product.objects.all().delete()
            Category.objects.all().delete()
            SkillTag.objects.all().delete()
            self.stdout.write(self.style.WARNING("All catalog data cleared."))

        self.stdout.write("Seeding categories...")
        parent_cats = self._seed_parent_categories()
        grade_cats = self._seed_child_categories(GRADE_CATEGORIES, parent_cats["by-grade"])
        focus_cats = self._seed_child_categories(FOCUS_CATEGORIES, parent_cats["by-focus"])
        format_cats = self._seed_child_categories(FORMAT_CATEGORIES, parent_cats["by-format"])

        self.stdout.write("Seeding skill tags...")
        skill_tag_map = self._seed_skill_tags()

        self.stdout.write("Seeding products...")
        sku_map = {}
        for defn in PRODUCT_DEFINITIONS:
            sku = self._seed_product(defn, grade_cats, focus_cats, format_cats, skill_tag_map)
            sku_map[defn["sku_code"]] = sku

        self.stdout.write("Seeding bundle product...")
        self._seed_bundle(BUNDLE_DEFINITION, grade_cats, focus_cats, format_cats, skill_tag_map, sku_map)

        self.stdout.write("Seeding shipping rates...")
        self._seed_shipping_rates()

        self.stdout.write("Seeding product images...")
        self._seed_product_images()

        self.stdout.write(self.style.SUCCESS("Seed complete."))

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _seed_parent_categories(self):
        result = {}
        for data in PARENT_CATEGORIES:
            cat, created = Category.objects.get_or_create(
                slug=data["slug"],
                defaults={
                    "name": data["name"],
                    "display_order": data["display_order"],
                    "is_active": True,
                },
            )
            result[data["slug"]] = cat
            verb = "Created" if created else "Exists"
            self.stdout.write(f"  {verb}: category '{cat.name}'")
        return result

    def _seed_child_categories(self, definitions, parent):
        result = {}
        for data in definitions:
            cat, created = Category.objects.get_or_create(
                slug=data["slug"],
                defaults={
                    "name": data["name"],
                    "parent": parent,
                    "display_order": data["display_order"],
                    "is_active": True,
                },
            )
            result[data["slug"]] = cat
            verb = "Created" if created else "Exists"
            self.stdout.write(f"  {verb}: category '{cat.name}' under '{parent.name}'")
        return result

    def _seed_skill_tags(self):
        result = {}
        for data in SKILL_TAGS:
            tag, created = SkillTag.objects.get_or_create(
                slug=data["slug"],
                defaults={
                    "name": data["name"],
                    "curriculum_standard": data.get("curriculum_standard", ""),
                },
            )
            result[data["slug"]] = tag
            verb = "Created" if created else "Exists"
            self.stdout.write(f"  {verb}: skill tag '{tag.name}'")
        return result

    def _seed_product(self, defn, grade_cats, focus_cats, format_cats, skill_tag_map):
        slug = slugify(defn["title"])[:255]

        product, created = Product.objects.get_or_create(
            slug=slug,
            defaults={
                "title": defn["title"],
                "product_type": defn["product_type"],
                "base_price": defn["base_price"],
                "description": defn["description"],
                "short_description": defn["short_description"],
                "format_specs": defn.get("format_specs", {}),
                "is_active": True,
                "is_featured": defn.get("is_featured", False),
                "seo_title": defn["title"],
                "seo_description": defn["short_description"],
            },
        )

        verb = "Created" if created else "Exists"
        self.stdout.write(f"  {verb}: product '{product.title}'")

        # Categories
        for grade_slug in defn.get("grades", []):
            if grade_slug in grade_cats:
                ProductCategory.objects.get_or_create(
                    product=product, category=grade_cats[grade_slug]
                )
        for focus_slug in defn.get("focus", []):
            if focus_slug in focus_cats:
                ProductCategory.objects.get_or_create(
                    product=product, category=focus_cats[focus_slug]
                )
        format_slug = defn.get("format")
        if format_slug and format_slug in format_cats:
            ProductCategory.objects.get_or_create(
                product=product, category=format_cats[format_slug]
            )

        # Skill tags
        for tag_slug in defn.get("skill_tags", []):
            if tag_slug in skill_tag_map:
                product.skill_tags.add(skill_tag_map[tag_slug])

        # SKU
        sku, sku_created = SKU.objects.get_or_create(
            sku_code=defn["sku_code"],
            defaults={"product": product, "is_active": True},
        )

        # Stock Level
        is_digital = defn["product_type"] == "digital"
        stock, stock_created = StockLevel.objects.get_or_create(
            sku=sku,
            defaults={
                "is_unlimited": is_digital,
                "quantity_on_hand": 0 if is_digital else random.randint(5, 50),
                "low_stock_threshold": 5,
                "backorder_enabled": False,
            },
        )

        if stock_created and not is_digital:
            StockMovement.objects.create(
                sku=sku,
                movement_type=StockMovement.MovementType.INITIAL,
                delta=stock.quantity_on_hand,
                quantity_after=stock.quantity_on_hand,
                reason="Initial seed stock",
            )

        return sku

    def _seed_product_images(self):
        """Download Creative Commons (Unsplash) images for every product that lacks one."""
        import io
        import urllib.request
        import urllib.error
        from django.core.files.base import ContentFile

        # Mapping of SKU codes to Unsplash image URLs (Unsplash License — free for
        # commercial and non-commercial use).
        IMAGE_URLS = {
            "DR-SET-A-CVC": "https://images.unsplash.com/photo-1533561304446-88a43deb6229?w=800&h=800&fit=crop",
            "DR-SET-B-DIG": "https://images.unsplash.com/photo-1512820790803-83ca734da794?w=800&h=800&fit=crop",
            "DR-SET-C-VT": "https://images.unsplash.com/photo-1524578271613-d550eacf6090?w=800&h=800&fit=crop",
            "TG-PHONICS-G1": "https://images.unsplash.com/photo-1503676260728-1c00da094a0b?w=800&h=800&fit=crop",
            "TG-PHONICS-G2": "https://images.unsplash.com/photo-1497633762265-9d179a990aa6?w=800&h=800&fit=crop",
            "TG-PA-PREK-K": "https://images.unsplash.com/photo-1588072432836-e10032774350?w=800&h=800&fit=crop",
            "WB-PHONICS-K": "https://images.unsplash.com/photo-1544776193-352d25ca82cd?w=800&h=800&fit=crop",
            "WB-PHONICS-G1": "https://images.unsplash.com/photo-1578593139939-cccb1e98698c?w=800&h=800&fit=crop",
            "WB-PHONICS-G2": "https://images.unsplash.com/photo-1602541975165-6ae912c931b7?w=800&h=800&fit=crop",
            "FLASH-SIGHT-220": "https://images.unsplash.com/photo-1632571401005-458e9d244591?w=800&h=800&fit=crop",
            "FP-FLUENCY-G1": "https://images.unsplash.com/photo-1530303388419-840456159b0d?w=800&h=800&fit=crop",
            "FP-FLUENCY-G2": "https://images.unsplash.com/photo-1541802802036-1d572ba70147?w=800&h=800&fit=crop",
            "VOC-BUILDER-G3": "https://images.unsplash.com/photo-1550376026-33cbee34f79e?w=800&h=800&fit=crop",
            "COMP-TOOLKIT-35": "https://images.unsplash.com/photo-1509062522246-3755977927d7?w=800&h=800&fit=crop",
            "PA-CARDS-K": "https://images.unsplash.com/photo-1573868401232-cbc9cd67c731?w=800&h=800&fit=crop",
            "POSTER-WFAM-24": "https://images.unsplash.com/photo-1580582932707-520aed937b7b?w=800&h=800&fit=crop",
            "DL-SCOPE-SEQ-K5": "https://images.unsplash.com/photo-1616861771635-49063a4636ed?w=800&h=800&fit=crop",
            "DL-WARMUP-K2": "https://images.unsplash.com/photo-1560439514-0fc9d2cd5e1b?w=800&h=800&fit=crop",
            "DL-PASSAGES-23": "https://images.unsplash.com/photo-1603406136476-85d8c3ec76a5?w=800&h=800&fit=crop",
            "TG-MULTI-G4": "https://images.unsplash.com/photo-1534337621606-e3df5ee0e97f?w=800&h=800&fit=crop",
            "KIT-G1-LITERACY": "https://images.unsplash.com/photo-1597831603708-71e01189ba2c?w=800&h=800&fit=crop",
        }

        for product in Product.objects.all():
            if product.images.exists():
                continue

            # Find the SKU code for this product
            sku = product.skus.first()
            if not sku:
                self.stdout.write(self.style.WARNING(f"  No SKU for '{product.title}' — skipping."))
                continue

            url = IMAGE_URLS.get(sku.sku_code)
            if not url:
                self.stdout.write(self.style.WARNING(f"  No image URL for SKU '{sku.sku_code}' — skipping."))
                continue

            try:
                req = urllib.request.Request(url, headers={"User-Agent": "UpstreamLiteracy/1.0"})
                with urllib.request.urlopen(req, timeout=30) as resp:
                    image_data = resp.read()
            except (urllib.error.URLError, OSError) as exc:
                self.stdout.write(self.style.WARNING(f"  Failed to download image for '{product.title}': {exc}"))
                continue

            filename = f"{product.slug}.jpg"
            pi = ProductImage(
                product=product,
                alt_text=product.title,
                is_primary=True,
                display_order=0,
            )
            pi.image.save(filename, ContentFile(image_data), save=True)
            self.stdout.write(f"  Downloaded image for '{product.title}'")

    def _seed_shipping_rates(self):
        rates = [
            {
                "name": "Standard Shipping",
                "flat_rate": "5.99",
                "estimated_days_min": 3,
                "estimated_days_max": 7,
                "description": "Delivered in 3–7 business days via USPS.",
                "is_active": True,
                "sort_order": 10,
            },
            {
                "name": "Expedited Shipping",
                "flat_rate": "12.99",
                "estimated_days_min": 1,
                "estimated_days_max": 3,
                "description": "Delivered in 1–3 business days via UPS.",
                "is_active": True,
                "sort_order": 20,
            },
        ]
        for data in rates:
            rate, created = ShippingRate.objects.get_or_create(
                name=data["name"],
                defaults=data,
            )
            verb = "Created" if created else "Exists"
            self.stdout.write(f"  {verb}: shipping rate '{rate.name}' (${rate.flat_rate})")

    def _seed_bundle(self, defn, grade_cats, focus_cats, format_cats, skill_tag_map, sku_map):
        slug = slugify(defn["title"])[:255]

        product, created = Product.objects.get_or_create(
            slug=slug,
            defaults={
                "title": defn["title"],
                "product_type": "bundle",
                "base_price": defn["base_price"],
                "description": defn["description"],
                "short_description": defn["short_description"],
                "format_specs": defn.get("format_specs", {}),
                "is_active": True,
                "is_featured": defn.get("is_featured", False),
                "seo_title": defn["title"],
                "seo_description": defn["short_description"],
            },
        )

        verb = "Created" if created else "Exists"
        self.stdout.write(f"  {verb}: bundle product '{product.title}'")

        # Categories
        for grade_slug in defn.get("grades", []):
            if grade_slug in grade_cats:
                ProductCategory.objects.get_or_create(
                    product=product, category=grade_cats[grade_slug]
                )
        for focus_slug in defn.get("focus", []):
            if focus_slug in focus_cats:
                ProductCategory.objects.get_or_create(
                    product=product, category=focus_cats[focus_slug]
                )
        format_slug = defn.get("format")
        if format_slug and format_slug in format_cats:
            ProductCategory.objects.get_or_create(
                product=product, category=format_cats[format_slug]
            )

        # Skill tags
        for tag_slug in defn.get("skill_tags", []):
            if tag_slug in skill_tag_map:
                product.skill_tags.add(skill_tag_map[tag_slug])

        # Bundle SKU
        sku, _ = SKU.objects.get_or_create(
            sku_code=defn["sku_code"],
            defaults={"product": product, "is_active": True},
        )

        # Bundle stock level (physical bundle)
        stock, stock_created = StockLevel.objects.get_or_create(
            sku=sku,
            defaults={
                "is_unlimited": False,
                "quantity_on_hand": random.randint(5, 20),
                "low_stock_threshold": 3,
                "backorder_enabled": False,
            },
        )
        if stock_created:
            StockMovement.objects.create(
                sku=sku,
                movement_type=StockMovement.MovementType.INITIAL,
                delta=stock.quantity_on_hand,
                quantity_after=stock.quantity_on_hand,
                reason="Initial seed stock",
            )

        # Bundle components
        for comp_defn in defn.get("components", []):
            component_sku = sku_map.get(comp_defn["sku_code"])
            if component_sku:
                BundleComponent.objects.get_or_create(
                    bundle_product=product,
                    component_sku=component_sku,
                    defaults={"quantity": comp_defn["quantity"]},
                )
                self.stdout.write(
                    f"    Component: {component_sku.sku_code} x{comp_defn['quantity']}"
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"    WARNING: Component SKU '{comp_defn['sku_code']}' not found."
                    )
                )
