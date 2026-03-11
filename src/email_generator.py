"""
📧 VectorBridge Email Generator v1.4
Location : src/email_generator.py
Input    : output/rich_matched_dataset.csv
Output   : output/generated_emails.csv
Run from : project root → python src/email_generator.py
"""
import sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

import pandas as pd
from groq import Groq
import time, os
from config import OUTPUT_DIR


# ─── CONFIG ───────────────────────────────────────────────────
GROQ_API_KEY      = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL        = "llama-3.3-70b-versatile"
DELAY_SECONDS     = 1.0
MAX_RETRIES       = 3
SKIP_WEAK_MATCHES = True          # rows where match_quality == "Weak"

INPUT_FILE  = OUTPUT_DIR / "rich_matched_dataset.csv"
OUTPUT_FILE = OUTPUT_DIR / "generated_emails.csv"

PROGRAM_NAME    = "VectorBridge Mentorship Program"
ORGANIZER_NAME  = "VectorBridge Team"
ORGANIZER_EMAIL = "mentorship@vectorbridge.io"
PROGRAM_TAGLINE = "Connecting talent to experience, one match at a time."


# ─── TEMPLATES ────────────────────────────────────────────────
MENTEE_TEMPLATE = """\
Hi [MENTEE_FIRST_NAME],

We're excited to share your mentor match through the {program} — {tagline}. \
We paired you with [MENTOR_FULL_NAME] because your interest in [MENTEE_MATCHED_SKILL] \
aligns directly with their expertise in [MENTOR_MATCHED_SKILL]. \
[1 SENTENCE: explain why this pairing makes practical sense — \
rephrase naturally if the skill relationship is indirect or nuanced, skip gracefully if context is thin.]

To get started, reach out to [MENTOR_FULL_NAME] via [CONTACT_PLATFORM] at [CONTACT_HANDLE]. \
A short intro message about yourself and your goals is a great first step. \
Warm regards, {organizer} ({organizer_email})
""".format(
    program=PROGRAM_NAME, tagline=PROGRAM_TAGLINE,
    organizer=ORGANIZER_NAME, organizer_email=ORGANIZER_EMAIL
)

MENTOR_TEMPLATE = """\
Hi [MENTOR_FIRST_NAME],

Thank you for being part of the {program} — {tagline}. \
We've matched you with [MENTEE_FULL_NAME] from the [MENTEE_DEPARTMENT] department, \
whose focus on [MENTEE_MATCHED_SKILL] is a strong fit with your expertise in [MENTOR_MATCHED_SKILL]. \
[1 SENTENCE: briefly explain why this pairing makes practical sense — \
rephrase naturally if the skill relationship is indirect or nuanced, skip gracefully if context is thin.]

You can reach [MENTEE_FULL_NAME] at [MENTEE_EMAIL]. \
Please try to connect within 3–5 days — even a brief intro works perfectly. \
Thank you for your time and generosity. \
Best regards, {organizer} ({organizer_email})
""".format(
    program=PROGRAM_NAME, tagline=PROGRAM_TAGLINE,
    organizer=ORGANIZER_NAME, organizer_email=ORGANIZER_EMAIL
)

SYSTEM_MSG = (
    "You fill in email templates for a mentorship program. "
    "Replace every [BRACKETED] placeholder with the exact value given. "
    "For the [1 SENTENCE] creative slot, write one natural sentence fitting the context. "
    "If any value is missing or 'N/A', rewrite that sentence fragment to omit it gracefully — never print 'N/A'. "
    "Output only the filled email body. No subject line. No extra paragraphs. No bullet points."
)


# ─── INIT CLIENT ──────────────────────────────────────────────
def init_client():
    if not GROQ_API_KEY:
        raise ValueError(
            "❌ GROQ_API_KEY not set.\n"
            "   Add GROQ_API_KEY=gsk_... to your .env file\n"
            "   Get a free key: https://console.groq.com/keys"
        )
    client = Groq(api_key=GROQ_API_KEY)
    print(f"✅ Groq client initialized — model: {GROQ_MODEL}")
    return client


# ─── HELPERS ──────────────────────────────────────────────────
def safe(val, fallback="N/A"):
    """Title-cased display value."""
    if pd.isna(val) or str(val).strip().lower() in ["", "nan", "none", "n/a"]:
        return fallback
    return str(val).strip().title()

def safe_raw(val, fallback="N/A"):
    """Raw value, no case change."""
    if pd.isna(val) or str(val).strip().lower() in ["", "nan", "none", "n/a"]:
        return fallback
    return str(val).strip()

def first_name(full_name):
    name = safe_raw(full_name)
    return name.split()[0].title() if name != "N/A" else "there"

def clean_email(val):
    """
    Strips markdown mailto format.
    '[arjun@gmail.com](mailto:arjun@gmail.com)' → 'arjun@gmail.com'
    Plain emails pass through unchanged.
    """
    raw = safe_raw(val)
    if raw == "N/A":
        return "N/A"
    # Match [text](mailto:...) format
    match = re.search(r'\[([^\]]+)\]\(mailto:[^)]+\)', raw)
    if match:
        return match.group(1).strip()
    # Match bare mailto: prefix
    if raw.startswith("mailto:"):
        return raw[7:].strip()
    return raw

def parse_contact(val):
    """
    Splits 'WhatsApp - +977-9827389659' → ('WhatsApp', '+977-9827389659')
    Splits 'LinkedIn - https://...'     → ('LinkedIn', 'https://...')
    Falls back to ('their preferred channel', val) if format unexpected.
    """
    raw = safe_raw(val)
    if raw == "N/A":
        return ("their preferred channel", "N/A")
    if " - " in raw:
        parts = raw.split(" - ", 1)
        return (parts[0].strip(), parts[1].strip())
    return ("their preferred channel", raw)

def format_area(area_str):
    if not area_str or safe_raw(area_str) == "N/A":
        return "skill area"
    return str(area_str).replace("_", " ").lower()

def build_context(row):
    """Build matched-pair context once per row."""
    return {
        "mentee_matched_skill": safe_raw(row.get("mentee_skill_text")),
        "mentor_matched_skill": safe_raw(row.get("mentor_skill_text")),
        "mentee_matched_area":  format_area(row.get("mentee_skill_area")),
        "mentor_matched_area":  format_area(row.get("mentor_skill_area")),
    }


# ─── GROQ CALL WITH RETRY ─────────────────────────────────────
def call_groq(client, system_msg, user_msg):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user",   "content": user_msg},
                ],
                temperature=0.3,
                max_tokens=550,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            if attempt == MAX_RETRIES:
                raise
            wait = 5 * attempt
            print(f"\n  ⚠️  Attempt {attempt} failed ({e}). Retrying in {wait}s...")
            time.sleep(wait)


# ─── EMAIL GENERATORS ─────────────────────────────────────────
def generate_mentee_email(client, row, ctx):
    platform, handle = parse_contact(row.get("mentor_contact_preference"))
    mentor_bg = safe_raw(row.get("mentor_work_affiliation"))

    user_msg = f"""
Fill in this EXACT template. Replace every [BRACKETED] slot using the data below.

TEMPLATE:
{MENTEE_TEMPLATE}

DATA:
- [MENTEE_FIRST_NAME]    = {first_name(row.get('mentee_name'))}
- [MENTOR_FULL_NAME]     = {safe(row.get('mentor_name'))}
- [MENTEE_MATCHED_SKILL] = {ctx['mentee_matched_skill']}
- [MENTOR_MATCHED_SKILL] = {ctx['mentor_matched_skill']}
- [CONTACT_PLATFORM]     = {platform}
- [CONTACT_HANDLE]       = {handle}
- Mentor background      : {mentor_bg}
"""
    return call_groq(client, SYSTEM_MSG, user_msg)


def generate_mentor_email(client, row, ctx):
    user_msg = f"""
Fill in this EXACT template. Replace every [BRACKETED] slot using the data below.

TEMPLATE:
{MENTOR_TEMPLATE}

DATA:
- [MENTOR_FIRST_NAME]    = {first_name(row.get('mentor_name'))}
- [MENTEE_FULL_NAME]     = {safe(row.get('mentee_name'))}
- [MENTEE_DEPARTMENT]    = {safe(row.get('mentee_department'))}
- [MENTEE_MATCHED_SKILL] = {ctx['mentee_matched_skill']}
- [MENTOR_MATCHED_SKILL] = {ctx['mentor_matched_skill']}
- [MENTEE_EMAIL]         = {clean_email(row.get('mentee_email'))}
- Mentor background      : {safe_raw(row.get('mentor_work_affiliation'))}
"""
    return call_groq(client, SYSTEM_MSG, user_msg)


# ─── SUBJECT LINES ────────────────────────────────────────────
def make_subjects(row):
    return (
        f"[VectorBridge] Your Mentor Match: {safe(row.get('mentor_name'))} 🎓",
        f"[VectorBridge] Your Mentee Match: {safe(row.get('mentee_name'))} 👋",
    )


# ─── MAIN ─────────────────────────────────────────────────────
def main():
    print("\n" + "="*70)
    print("📧 VECTORBRIDGE EMAIL GENERATOR v1.4")
    print(f"   Powered by Groq — {GROQ_MODEL}")
    print("="*70)

    if not INPUT_FILE.exists():
        print(f"❌ Input not found: {INPUT_FILE}")
        print("   Run matching_algorithm.py first.")
        return

    df    = pd.read_csv(INPUT_FILE)
    total = len(df)
    print(f"\n✓ Loaded {total} matched pairs from {INPUT_FILE.name}")

    required = ["mentee_skill_text", "mentor_skill_text",
                "mentee_skill_area",  "mentor_skill_area"]
    missing  = [c for c in required if c not in df.columns]
    if missing:
        print(f"⚠️  Missing columns: {missing}")
    else:
        print("✓ Matched skill columns present ✅")

    # Warn about weak matches
    weak = (df["match_quality"].str.lower() == "weak").sum()
    if weak:
        action = "skipping" if SKIP_WEAK_MATCHES else "including"
        print(f"⚠️  {weak} Weak match(es) found — {action}")

    df["mentee_subject"]    = ""
    df["mentee_email_body"] = ""
    df["mentor_subject"]    = ""
    df["mentor_email_body"] = ""
    df["generation_status"] = ""

    processed = 0
    print("\n" + "─"*70)

    for idx, row in df.iterrows():
        pair_num    = idx + 1
        mentee_name = safe(row.get("mentee_name"))
        mentor_name = safe(row.get("mentor_name"))
        quality     = safe_raw(row.get("match_quality"))
        pair_str    = (
            f"{safe_raw(row.get('mentee_skill_text', '?'))[:20]}"
            f" ↔ {safe_raw(row.get('mentor_skill_text', '?'))[:20]}"
        )

        print(f"\n[{pair_num:>3}/{total}] {mentee_name[:20]:20} ↔ "
              f"{mentor_name[:20]:20} | {quality}")
        print(f"         Pair   : {pair_str}")

        # Skip weak matches
        if SKIP_WEAK_MATCHES and quality.lower() == "weak":
            print(f"         ⏭  Skipped (Weak match)")
            df.at[idx, "generation_status"] = "skipped: weak match"
            continue

        try:
            ctx = build_context(row)

            print(f"         ✉  Mentee email...", end=" ", flush=True)
            mentee_body = generate_mentee_email(client, row, ctx)
            print("✓")
            time.sleep(DELAY_SECONDS)

            print(f"         ✉  Mentor email...", end=" ", flush=True)
            mentor_body = generate_mentor_email(client, row, ctx)
            print("✓")
            time.sleep(DELAY_SECONDS)

            mentee_subj, mentor_subj = make_subjects(row)

            df.at[idx, "mentee_subject"]    = mentee_subj
            df.at[idx, "mentee_email_body"] = mentee_body
            df.at[idx, "mentor_subject"]    = mentor_subj
            df.at[idx, "mentor_email_body"] = mentor_body
            df.at[idx, "generation_status"] = "success"
            processed += 1

        except Exception as e:
            print(f"\n  ⚠️  FAILED for pair {pair_num}: {e}")
            df.at[idx, "generation_status"] = f"failed: {e}"
            df.to_csv(OUTPUT_FILE, index=False)   # save immediately on failure
            continue

        if pair_num % 10 == 0:
            df.to_csv(OUTPUT_FILE, index=False)
            print(f"\n  💾 Checkpoint saved ({pair_num}/{total})\n")
            print("─"*70)

    df.to_csv(OUTPUT_FILE, index=False)

    success = (df["generation_status"] == "success").sum()
    skipped = (df["generation_status"].str.startswith("skipped")).sum()
    failed  = total - success - skipped

    print("\n" + "="*70)
    print("✅ VECTORBRIDGE EMAIL GENERATION COMPLETE")
    print(f"   ✓ Success  : {success} pairs ({success*2} emails)")
    print(f"   ⏭  Skipped  : {skipped} (weak matches)")
    if failed:
        print(f"   ⚠️  Failed  : {failed} — check 'generation_status' column")
    print(f"   📄 Output  : {OUTPUT_FILE}")
    print(f"\n⚠️  REVIEW generated_emails.csv BEFORE SENDING")
    print("="*70)


if __name__ == "__main__":
    try:
        client = init_client()
    except ValueError as e:
        print(e)
        sys.exit(1)
    main()
