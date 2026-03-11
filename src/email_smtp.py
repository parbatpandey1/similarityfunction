"""
📤 VectorBridge Email Sender v3.0 — Gmail SMTP
Reads output/generated_emails.csv → sends via Gmail SMTP.
Run: python src/email_sender.py
"""
import sys, os, re, time, smtplib
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

sys.path.insert(0, str(Path(__file__).parent))
from dotenv import load_dotenv
load_dotenv()

import pandas as pd
from config import OUTPUT_DIR


# ─── CONFIG ───────────────────────────────────────────────────
GMAIL_USER     = os.environ.get("GMAIL_USER", "")
GMAIL_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
SENDER_DISPLAY = "VectorBridge Mentorship"
INPUT_FILE     = OUTPUT_DIR / "generated_emails.csv"
OUTPUT_FILE    = OUTPUT_DIR / "sent_log.csv"
DRY_RUN        = False
TEST_MODE      = True
TEST_EMAIL     = "parbat1256@gmail.com"
TEST_ONE_PAIR  = True      # ← set False to send all pairs
DELAY_SECONDS  = 3.0       # Gmail needs breathing room
BRAND_COLOR    = "#4F46E5"


# ─── HTML BUILDER ─────────────────────────────────────────────
def body_to_html(body_text: str) -> str:
    body_text = body_text.replace("\r\n", "\n").strip()
    parts     = [p.strip() for p in body_text.split("\n\n") if p.strip()]

    greeting  = parts[0] if len(parts) >= 1 else ""
    para1     = parts[1] if len(parts) >= 2 else ""
    last_part = parts[2] if len(parts) >= 3 else ""

    signoff_match = re.search(
        r'(Warm regards.*|Best regards.*)',
        last_part, re.IGNORECASE
    )
    if signoff_match:
        para2   = last_part[:signoff_match.start()].strip()
        signoff = last_part[signoff_match.start():].strip()
    else:
        para2   = last_part
        signoff = ""

    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0; padding:0; background:#f4f4f5; font-family:Arial,sans-serif;">

  <table width="100%" cellpadding="0" cellspacing="0"
         style="background:#f4f4f5; padding:32px 16px;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0"
             style="background:#fff; border-radius:8px;
                    box-shadow:0 1px 6px rgba(0,0,0,0.08);
                    overflow:hidden; max-width:600px; width:100%;">

        <!-- Header -->
        <tr>
          <td style="background:{BRAND_COLOR}; padding:20px 32px;">
            <span style="color:#fff; font-size:17px; font-weight:700;
                         letter-spacing:0.4px;">⚡ VectorBridge Mentorship</span>
          </td>
        </tr>

        <!-- Greeting -->
        <tr>
          <td style="padding:28px 32px 0 32px; color:#1f2937; font-size:15px;">
            <p style="margin:0; font-weight:600;">{greeting}</p>
          </td>
        </tr>

        <!-- Paragraph 1 -->
        <tr>
          <td style="padding:16px 32px 0 32px; color:#374151;
                     font-size:15px; line-height:1.7;">
            <p style="margin:0;">{para1}</p>
          </td>
        </tr>

        <!-- Paragraph 2 -->
        <tr>
          <td style="padding:16px 32px 0 32px; color:#374151;
                     font-size:15px; line-height:1.7;">
            <p style="margin:0;">{para2}</p>
          </td>
        </tr>

        <!-- Sign-off -->
        <tr>
          <td style="padding:20px 32px 28px 32px;
                     border-top:1px solid #e5e7eb;">
            <p style="margin:12px 0 4px 0; color:#4b5563;
                      font-size:14px; font-weight:600;">{signoff}</p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>

</body>
</html>
"""


# ─── MIME BUILDER ─────────────────────────────────────────────
def build_mime(to_email: str, subject: str, body_text: str) -> MIMEMultipart:
    msg = MIMEMultipart("alternative")
    msg["From"]    = f"{SENDER_DISPLAY} <{GMAIL_USER}>"
    msg["To"]      = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body_text,               "plain", "utf-8"))
    msg.attach(MIMEText(body_to_html(body_text),  "html",  "utf-8"))
    return msg


# ─── SEND ONE EMAIL ───────────────────────────────────────────
def send_one(smtp, to_email: str, subject: str, body_text: str, label: str) -> str:
    actual_to  = TEST_EMAIL if TEST_MODE else to_email
    tag        = "→ TEST"   if TEST_MODE else "✓ sent"
    subj_final = f"[TEST] {subject}" if TEST_MODE else subject

    try:
        msg = build_mime(actual_to, subj_final, body_text)
        if not DRY_RUN:
            smtp.sendmail(GMAIL_USER, actual_to, msg.as_string())
        print(f"   ✉  {label:7} → {actual_to:45} {tag}")
        return "test_sent" if TEST_MODE else "sent"
    except Exception as e:
        print(f"   ⚠️  {label:7} → {actual_to} FAILED: {e}")
        return f"failed: {e}"


# ─── MAIN ─────────────────────────────────────────────────────
def main():
    mode_str = (
        "DRY RUN" if DRY_RUN else
        ("TEST → " + TEST_EMAIL if TEST_MODE else "🚀 LIVE SEND")
    )
    print("\n" + "="*65)
    print("📤 VECTORBRIDGE EMAIL SENDER v3.0 — Gmail SMTP")
    print(f"   Mode  : {mode_str}")
    if TEST_ONE_PAIR:
        print("   Pairs : first pair only (2 emails)")
    print("="*65)

    if not DRY_RUN and (not GMAIL_USER or not GMAIL_PASSWORD):
        print("❌ GMAIL_USER or GMAIL_APP_PASSWORD missing in .env")
        print("   Get App Password: myaccount.google.com/apppasswords")
        return

    if not INPUT_FILE.exists():
        print(f"❌ {INPUT_FILE} not found. Run email_generator.py first.")
        return

    df       = pd.read_csv(INPUT_FILE)
    sendable = df[df["generation_status"] == "success"]
    skipped  = df[df["generation_status"] != "success"]

    print(f"\n✓ {len(df)} total rows loaded")
    print(f"  → {len(sendable)} pairs ready  ({len(sendable) * 2} emails)")
    print(f"  → {len(skipped)} skipped (weak/failed)")
    if not TEST_MODE and not DRY_RUN:
        print(f"  → Gmail daily limit used: {len(sendable) * 2}/500")
    print("\n" + "─"*65)

    df["mentee_send_status"] = ""
    df["mentor_send_status"] = ""

    with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        if not DRY_RUN:
            smtp.login(GMAIL_USER, GMAIL_PASSWORD)
            print("✅ Gmail authenticated\n")

        for idx, row in df.iterrows():
            pair_num = idx + 1

            if row["generation_status"] != "success":
                df.at[idx, "mentee_send_status"] = "skipped"
                df.at[idx, "mentor_send_status"] = "skipped"
                continue

            print(f"\n[{pair_num:>2}] {row['mentee_name']:25} ↔  {row['mentor_name']}")

            df.at[idx, "mentee_send_status"] = send_one(
                smtp,
                to_email  = row["mentee_email"],
                subject   = row["mentee_subject"],
                body_text = row["mentee_email_body"],
                label     = "Mentee",
            )
            time.sleep(DELAY_SECONDS)

            df.at[idx, "mentor_send_status"] = send_one(
                smtp,
                to_email  = row["mentor_email"],
                subject   = row["mentor_subject"],
                body_text = row["mentor_email_body"],
                label     = "Mentor",
            )
            time.sleep(DELAY_SECONDS)

            # Save after every pair — no progress lost on failure
            df.to_csv(OUTPUT_FILE, index=False)

            if TEST_ONE_PAIR:
                break   # ← remove when ready for full send

    df.to_csv(OUTPUT_FILE, index=False)

    tag    = "dry_run" if DRY_RUN else ("test_sent" if TEST_MODE else "sent")
    sent   = (df["mentee_send_status"] == tag).sum()
    failed = df["mentee_send_status"].str.startswith("failed", na=False).sum()

    print("\n" + "="*65)
    print("✅ DONE")
    print(f"   ✓ {sent} pairs ({sent * 2} emails) [{tag}]")
    if failed:
        print(f"   ⚠️  {failed} failed — check sent_log.csv")
    print(f"   📄 Log: {OUTPUT_FILE}")
    if TEST_MODE and not DRY_RUN:
        print(f"\n   → Check {TEST_EMAIL} in Gmail.")
        print("   → Happy? Set TEST_MODE=False, TEST_ONE_PAIR=False to send for real.")
    print("="*65)


if __name__ == "__main__":
    main()
