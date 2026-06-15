import os
import sys
import json
from dotenv import load_dotenv

load_dotenv()

from data_fetcher import fetch_all_market_data
from analyzer import analyze_market
from emailer import build_html
from github_publisher import publish

CI_MODE = "--ci" in sys.argv  # Running inside GitHub Actions


def _send_link_email(url: str):
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from datetime import date

    user = os.environ["GMAIL_USER"]
    pwd = os.environ["GMAIL_APP_PASSWORD"]
    month = date.today().strftime("%B %Y")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"TraderMind — {month} report is ready"
    msg["From"] = f"TraderMind <{user}>"
    msg["To"] = user

    html = f"""<div style="font-family:sans-serif;background:#0f172a;padding:40px;text-align:center;">
      <h1 style="color:#f8fafc;font-size:28px;margin-bottom:8px;">TraderMind</h1>
      <p style="color:#94a3b8;margin-bottom:28px;">Your {month} investment picks are ready.</p>
      <a href="{url}" style="background:#3b82f6;color:#fff;padding:14px 32px;border-radius:10px;text-decoration:none;font-size:16px;font-weight:600;">Open Report →</a>
      <p style="color:#475569;font-size:12px;margin-top:28px;">{url}</p>
    </div>"""

    msg.attach(MIMEText(f"Your TraderMind report for {month} is ready: {url}", "plain"))
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(user, pwd)
        server.sendmail(user, user, msg.as_string())
    print(f"Link emailed to {user}")


def check_env():
    required = ["ANTHROPIC_API_KEY"]
    if not CI_MODE:
        required.append("GITHUB_TOKEN")
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        print(f"ERROR: Missing environment variables: {', '.join(missing)}")
        print("Edit the .env file and fill in the values.")
        sys.exit(1)


def main():
    local_preview = "--local" in sys.argv
    publish_only = "--publish-only" in sys.argv

    if not local_preview:
        check_env()

    print("=== TraderMind Monthly Report ===\n")

    if publish_only:
        if not os.path.exists("last_analysis.json") or not os.path.exists("last_report.html"):
            print("ERROR: No saved analysis found. Run without --publish-only first.")
            sys.exit(1)
        print("Loading saved analysis...")
        with open("last_analysis.json", encoding="utf-8") as f:
            analysis = json.load(f)
        with open("last_report.html", encoding="utf-8") as f:
            html = f.read()
    else:
        market_data = fetch_all_market_data()
        analysis = analyze_market(market_data)
        html = build_html(analysis)

        with open("last_report.html", "w", encoding="utf-8") as f:
            f.write(html)
        with open("last_analysis.json", "w", encoding="utf-8") as f:
            json.dump(analysis, f, indent=2)
        print("Local backup saved: last_report.html + last_analysis.json")

    if local_preview:
        import webbrowser
        webbrowser.open(f"file://{os.path.abspath('last_report.html')}")
        print("Opened preview in browser.")
        return

    url = "https://filipczukkuba-spec.github.io/tradermind/"

    if CI_MODE:
        # In GitHub Actions: just write index.html — the workflow commits it
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(html)
        with open("latest.json", "w", encoding="utf-8") as f:
            json.dump(analysis, f, indent=2)
        print("Files written for GitHub Actions to commit.")
    else:
        url = publish(html, analysis)

    if os.environ.get("GMAIL_APP_PASSWORD"):
        _send_link_email(url)

    if not CI_MODE:
        print(f"\nDone! Opening your report...")
        import time, webbrowser
        time.sleep(5)
        webbrowser.open(url)
    else:
        print(f"\nDone! Report will be live at: {url}")


if __name__ == "__main__":
    main()
