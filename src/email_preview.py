"""
👁  VectorBridge Email Previewer
Generates HTML preview files from generated_emails.csv.

Run   : python src/email_preview.py
Output: output/previews/pair_01_mentee.html
        output/previews/pair_01_mentor.html  ...etc
"""
import sys, os, re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from dotenv import load_dotenv
load_dotenv()

import pandas as pd
from config import OUTPUT_DIR


INPUT_FILE   = OUTPUT_DIR / "generated_emails.csv"
PREVIEW_DIR  = OUTPUT_DIR / "previews"
BRAND_COLOR  = "#4F46E5"


# ─── reuse exact same builder from email_sender.py ────────────
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


# ─── WRAP WITH PREVIEW TOOLBAR ────────────────────────────────
def wrap_with_toolbar(html: str, subject: str, to: str,
                      pair_num: int, total: int,
                      prev_file: str, next_file: str) -> str:
    """Adds a top nav bar so you can flip through all previews in browser."""
    prev_btn = f'<a href="{prev_file}" style="{btn_style}">← Prev</a>' \
               if prev_file else f'<span style="{btn_style}; opacity:0.3;">← Prev</span>'
    next_btn = f'<a href="{next_file}" style="{btn_style}">Next →</a>' \
               if next_file else f'<span style="{btn_style}; opacity:0.3;">Next →</span>'

    toolbar = f"""
<div style="position:sticky; top:0; z-index:999; background:#1e1e2e;
            padding:10px 24px; display:flex; align-items:center;
            gap:16px; font-family:monospace; font-size:13px; color:#cdd6f4;
            border-bottom:2px solid {BRAND_COLOR};">
  {prev_btn}
  <span style="flex:1; text-align:center;">
    <b style="color:#cba6f7;">[{pair_num}/{total}]</b>
    &nbsp;To: <b style="color:#a6e3a1;">{to}</b>
    &nbsp;|&nbsp; Subject: <i style="color:#f9e2af;">{subject}</i>
  </span>
  {next_btn}
</div>
"""
    return toolbar + html

btn_style = (
    "color:#cdd6f4; background:#313244; padding:5px 14px; "
    "border-radius:4px; text-decoration:none; font-size:13px;"
)


# ─── MAIN ─────────────────────────────────────────────────────
def main():
    print("\n" + "="*60)
    print("👁  VECTORBRIDGE EMAIL PREVIEWER")
    print("="*60)

    if not INPUT_FILE.exists():
        print(f"❌ {INPUT_FILE} not found. Run email_generator.py first.")
        return

    df = pd.read_csv(INPUT_FILE)
    df = df[df["generation_status"] == "success"].reset_index(drop=True)

    if df.empty:
        print("❌ No successful rows found in CSV.")
        return

    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)

    # Build full file list first (needed for prev/next links)
    file_list = []
    for idx, row in df.iterrows():
        n = idx + 1
        file_list.append(PREVIEW_DIR / f"pair_{n:02d}_mentee.html")
        file_list.append(PREVIEW_DIR / f"pair_{n:02d}_mentor.html")

    total      = len(file_list)
    file_idx   = 0

    for idx, row in df.iterrows():
        n = idx + 1

        for role in ["mentee", "mentor"]:
            body_col   = f"{role}_email_body"
            subject_col = f"{role}_subject"
            email_col  = f"{role}_email"
            name_col   = f"{role}_name"

            body    = str(row[body_col])
            subject = str(row[subject_col])
            to      = f"{row[name_col]} <{row[email_col]}>"

            prev_f = file_list[file_idx - 1].name if file_idx > 0 else None
            next_f = file_list[file_idx + 1].name if file_idx < total - 1 else None

            html   = body_to_html(body)
            final  = wrap_with_toolbar(html, subject, to,
                                       file_idx + 1, total,
                                       prev_f, next_f)

            out_path = file_list[file_idx]
            out_path.write_text(final, encoding="utf-8")
            print(f"  ✓ {out_path.name}")
            file_idx += 1

    first = file_list[0].resolve()
    print(f"\n✅ {total} preview files saved to output/previews/")
    print(f"\n   Open in browser:")
    print(f"   → file://{first}")
    print("\n   Use ← → buttons in the toolbar to flip through all emails.")
    print("="*60)


if __name__ == "__main__":
    main()
