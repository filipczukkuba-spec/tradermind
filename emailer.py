import os
from datetime import date


RISK_COLOR = {"Low": "#22c55e", "Medium": "#f59e0b", "High": "#ef4444"}
CONVICTION_COLOR = {"High": "#818cf8", "Medium": "#94a3b8", "Speculative": "#f97316"}
ASSET_ICON = {"Stock": "📈", "ETF": "🗂️", "Sector ETF": "🏭", "Macro": "🌍"}
MACD_LABEL = {
    "bullish_accelerating": ("▲▲ Bullish Accelerating", "#22c55e"),
    "bullish": ("▲ Bullish", "#86efac"),
    "bearish": ("▼ Bearish", "#fca5a5"),
    "bearish_accelerating": ("▼▼ Bearish Accelerating", "#ef4444"),
}
REGIME_COLOR = {
    "early_bull": "#22c55e", "late_bull": "#86efac",
    "transition": "#f59e0b", "risk_off": "#ef4444",
    "early_bear": "#fca5a5", "late_bear": "#ef4444",
}


def _signal_pill(label: str, color: str) -> str:
    return f"<span style='background:{color}22;color:{color};padding:2px 8px;border-radius:12px;font-size:11px;font-weight:600;margin-right:4px;'>{label}</span>"


def _rsi_color(rsi) -> str:
    if rsi is None: return "#94a3b8"
    if rsi > 70: return "#ef4444"
    if rsi > 55: return "#22c55e"
    if rsi < 35: return "#f97316"
    return "#94a3b8"


def _pick_card(pick: dict) -> str:
    risk_col = RISK_COLOR.get(pick.get("risk_level", "Medium"), "#f59e0b")
    conv_col = CONVICTION_COLOR.get(pick.get("conviction", "Medium"), "#94a3b8")
    icon = ASSET_ICON.get(pick.get("asset_type", "Stock"), "📈")
    alloc = pick.get("allocation_pct", "")

    # Signal pills
    signals_html = ""
    macd = pick.get("signal_summary", "")
    rsi_val = None
    signals_html = f"<p style='color:#94a3b8;font-size:13px;margin:0 0 12px 0;'>{pick.get('signal_summary','')}</p>"

    # Trader voices
    voices_html = ""
    tv = pick.get("trader_voices", {})
    voice_map = [("soros","Soros"),("livermore","Livermore"),("tudor_jones","Tudor Jones"),("druckenmiller","Druckenmiller"),("simons","Simons")]
    for key, label in voice_map:
        if tv.get(key):
            voices_html += f"""<div style="margin-bottom:10px;">
              <span style="color:#7dd3fc;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;">{label}</span>
              <p style="margin:3px 0 0 0;color:#cbd5e1;font-size:13px;line-height:1.5;">{tv[key]}</p>
            </div>"""

    entry = pick.get("entry_note", "")
    stop = pick.get("stop_loss_idea", "")
    target = pick.get("price_target_rationale", "")

    return f"""
    <div style="background:#1e293b;border-radius:16px;padding:28px;margin-bottom:24px;border:1px solid #334155;">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px;margin-bottom:16px;">
        <div>
          <span style="font-size:26px;font-weight:800;color:#f8fafc;">{icon} {pick['symbol']}</span>
          <span style="color:#64748b;font-size:15px;margin-left:8px;">{pick.get('name','')}</span>
          <div style="margin-top:6px;">
            {_signal_pill(pick.get("risk_level","?") + " Risk", risk_col)}
            {_signal_pill(pick.get("conviction","?") + " Conviction", conv_col)}
            {_signal_pill(pick.get("asset_type",""), "#7dd3fc")}
          </div>
        </div>
        <div style="text-align:right;">
          <div style="font-size:24px;font-weight:700;color:#38bdf8;">${pick.get('current_price','')}</div>
          {f'<div style="margin-top:4px;background:#1e3a5f;color:#7dd3fc;padding:3px 12px;border-radius:20px;font-size:13px;display:inline-block;">Allocate {alloc}%</div>' if alloc else ''}
        </div>
      </div>

      <div style="background:#0f172a;border-radius:10px;padding:16px;margin-bottom:14px;">
        <div style="color:#64748b;font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:6px;">Thesis</div>
        <p style="color:#e2e8f0;font-size:14px;line-height:1.65;margin:0;">{pick.get('thesis','')}</p>
      </div>

      <div style="background:#0f172a;border-radius:10px;padding:14px;margin-bottom:14px;">
        <div style="color:#64748b;font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:6px;">Signal Confluence</div>
        <p style="color:#a5b4fc;font-size:13px;line-height:1.5;margin:0;">{pick.get('signal_summary','')}</p>
      </div>

      <div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:14px;">
        <div style="flex:1;min-width:130px;background:#0f172a;border-radius:10px;padding:12px;">
          <div style="color:#64748b;font-size:10px;text-transform:uppercase;letter-spacing:0.05em;">Hold Period</div>
          <div style="color:#f8fafc;font-size:15px;font-weight:600;margin-top:3px;">⏳ {pick.get('hold_period','')}</div>
        </div>
        {f'<div style="flex:1;min-width:130px;background:#0f172a;border-radius:10px;padding:12px;"><div style="color:#64748b;font-size:10px;text-transform:uppercase;letter-spacing:0.05em;">Entry Note</div><div style="color:#fbbf24;font-size:13px;margin-top:3px;">{entry}</div></div>' if entry else ''}
        {f'<div style="flex:1;min-width:130px;background:#450a0a;border-radius:10px;padding:12px;"><div style="color:#fca5a5;font-size:10px;text-transform:uppercase;letter-spacing:0.05em;">Stop Loss</div><div style="color:#fee2e2;font-size:13px;margin-top:3px;">{stop}</div></div>' if stop else ''}
      </div>

      <div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:14px;">
        <div style="flex:1;min-width:160px;background:#052e16;border-left:3px solid #22c55e;border-radius:0 8px 8px 0;padding:12px;">
          <div style="color:#86efac;font-size:11px;font-weight:600;">BULL CASE</div>
          <p style="color:#d1fae5;font-size:13px;margin:4px 0 0 0;">{pick.get('upside_scenario','')}</p>
        </div>
        <div style="flex:1;min-width:160px;background:#450a0a;border-left:3px solid #ef4444;border-radius:0 8px 8px 0;padding:12px;">
          <div style="color:#fca5a5;font-size:11px;font-weight:600;">BEAR CASE</div>
          <p style="color:#fee2e2;font-size:13px;margin:4px 0 0 0;">{pick.get('downside_risk','')}</p>
        </div>
      </div>

      {f'<div style="background:#0f172a;border-radius:10px;padding:12px;margin-bottom:14px;"><div style="color:#64748b;font-size:10px;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:4px;">Price Target Rationale</div><p style="color:#94a3b8;font-size:13px;margin:0;">{target}</p></div>' if target else ''}

      <details>
        <summary style="color:#7dd3fc;cursor:pointer;font-size:13px;font-weight:600;padding:4px 0;">Trader Voices ▾</summary>
        <div style="margin-top:10px;padding:14px;background:#0f172a;border-radius:8px;">{voices_html}</div>
      </details>
    </div>"""


def build_html(analysis: dict) -> str:
    today = date.today().strftime("%B %d, %Y")
    picks_html = "".join(_pick_card(p) for p in analysis.get("picks", []))

    regime = analysis.get("macro_regime", {})
    regime_class = regime.get("classification", "")
    regime_col = REGIME_COLOR.get(regime_class, "#94a3b8")
    regime_risks = "".join(f"<li style='color:#fca5a5;'>{r}</li>" for r in regime.get("key_risks", []))
    regime_tailwinds = "".join(f"<li style='color:#86efac;'>{t}</li>" for t in regime.get("key_tailwinds", []))

    contrarian = analysis.get("contrarian_watch", "")

    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>TraderMind — {today}</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{ margin:0; padding:0; background:#0f172a; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; }}
    details summary {{ list-style:none; }}
    details summary::-webkit-details-marker {{ display:none; }}
  </style>
</head>
<body>
  <div style="max-width:700px;margin:0 auto;padding:24px 16px 60px;">

    <!-- Header -->
    <div style="text-align:center;padding:48px 0 36px;">
      <div style="font-size:11px;color:#475569;text-transform:uppercase;letter-spacing:0.12em;margin-bottom:10px;">Monthly Investment Intelligence · {today}</div>
      <h1 style="color:#f8fafc;font-size:42px;font-weight:900;margin:0;letter-spacing:-0.02em;">TraderMind</h1>
      <p style="color:#475569;font-size:13px;margin:10px 0 0 0;letter-spacing:0.05em;">SOROS · LIVERMORE · TUDOR JONES · SIMONS · DRUCKENMILLER</p>
    </div>

    <!-- Macro Regime -->
    <div style="background:#1e293b;border-radius:16px;padding:24px;margin-bottom:20px;border:1px solid #334155;border-top:3px solid {regime_col};">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;">
        <h2 style="color:#f8fafc;font-size:16px;font-weight:700;margin:0;">Macro Regime</h2>
        <span style="background:{regime_col}22;color:{regime_col};padding:3px 12px;border-radius:20px;font-size:12px;font-weight:700;text-transform:uppercase;">{regime_class.replace('_',' ')}</span>
      </div>
      <p style="color:#e2e8f0;font-size:14px;line-height:1.65;margin:0 0 14px 0;">{regime.get('summary','')}</p>
      <div style="display:flex;gap:16px;flex-wrap:wrap;">
        {f'<div style="flex:1;min-width:180px;"><div style="color:#fca5a5;font-size:11px;font-weight:600;margin-bottom:4px;">KEY RISKS</div><ul style="margin:0;padding-left:16px;">{regime_risks}</ul></div>' if regime_risks else ''}
        {f'<div style="flex:1;min-width:180px;"><div style="color:#86efac;font-size:11px;font-weight:600;margin-bottom:4px;">TAILWINDS</div><ul style="margin:0;padding-left:16px;">{regime_tailwinds}</ul></div>' if regime_tailwinds else ''}
      </div>
    </div>

    <!-- Market + Macro -->
    <div style="display:flex;gap:16px;flex-wrap:wrap;margin-bottom:20px;">
      <div style="flex:1;min-width:260px;background:#1e293b;border-radius:16px;padding:20px;border:1px solid #334155;">
        <h2 style="color:#7dd3fc;font-size:12px;text-transform:uppercase;letter-spacing:0.06em;margin:0 0 10px 0;">Market Assessment</h2>
        <p style="color:#e2e8f0;font-size:14px;line-height:1.65;margin:0;">{analysis.get('market_summary','')}</p>
      </div>
      <div style="flex:1;min-width:260px;background:#1e293b;border-radius:16px;padding:20px;border:1px solid #334155;">
        <h2 style="color:#a78bfa;font-size:12px;text-transform:uppercase;letter-spacing:0.06em;margin:0 0 10px 0;">Macro Environment</h2>
        <p style="color:#e2e8f0;font-size:14px;line-height:1.65;margin:0;">{analysis.get('macro_environment','')}</p>
      </div>
    </div>

    <!-- Sector View -->
    <div style="background:#1e293b;border-radius:16px;padding:20px;margin-bottom:28px;border:1px solid #334155;">
      <h2 style="color:#34d399;font-size:12px;text-transform:uppercase;letter-spacing:0.06em;margin:0 0 10px 0;">Sector Rotation View</h2>
      <p style="color:#e2e8f0;font-size:14px;line-height:1.65;margin:0;">{analysis.get('sector_view','')}</p>
    </div>

    <!-- Picks -->
    <h2 style="color:#f8fafc;font-size:22px;font-weight:700;margin:0 0 18px 0;">This Month's Picks</h2>
    {picks_html}

    <!-- Avoid -->
    <div style="background:#1e293b;border-radius:16px;padding:20px;margin-bottom:20px;border:1px solid #7f1d1d;">
      <h2 style="color:#fca5a5;font-size:12px;text-transform:uppercase;letter-spacing:0.06em;margin:0 0 10px 0;">⚠ What to Avoid This Month</h2>
      <p style="color:#e2e8f0;font-size:14px;line-height:1.65;margin:0;">{analysis.get('what_to_avoid','')}</p>
    </div>

    <!-- Contrarian Watch -->
    {f'<div style="background:#1e293b;border-radius:16px;padding:20px;margin-bottom:20px;border:1px solid #334155;border-left:3px solid #f59e0b;"><h2 style="color:#fbbf24;font-size:12px;text-transform:uppercase;letter-spacing:0.06em;margin:0 0 10px 0;">👁 Contrarian Watch (Next Month)</h2><p style="color:#e2e8f0;font-size:14px;line-height:1.65;margin:0;">{contrarian}</p></div>' if contrarian else ''}

    <!-- Closing -->
    <div style="text-align:center;padding:32px 0;">
      <p style="color:#64748b;font-size:16px;font-style:italic;line-height:1.7;max-width:500px;margin:0 auto;">"{analysis.get('closing_thoughts','')}"</p>
    </div>

    <!-- Footer -->
    <div style="border-top:1px solid #1e293b;padding-top:16px;text-align:center;">
      <p style="color:#1e293b;font-size:11px;line-height:1.6;color:#334155;">AI-generated investment research for informational purposes only. Not financial advice. Past analysis does not guarantee future returns. Always assess your personal risk tolerance before investing.</p>
    </div>
  </div>
</body>
</html>"""


def send_email(analysis: dict):
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    gmail_user = os.environ["GMAIL_USER"]
    gmail_pass = os.environ["GMAIL_APP_PASSWORD"]
    recipient = os.environ.get("RECIPIENT_EMAIL", gmail_user)
    today = date.today().strftime("%B %Y")
    html_content = build_html(analysis)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"TraderMind — {today}"
    msg["From"] = f"TraderMind <{gmail_user}>"
    msg["To"] = recipient
    picks = analysis.get("picks", [])
    plain = f"TraderMind — {today}\n\n"
    for p in picks:
        plain += f"• {p['symbol']} ({p.get('hold_period','')}) — {p.get('thesis','')[:120]}...\n"
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html_content, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(gmail_user, gmail_pass)
        server.sendmail(gmail_user, recipient, msg.as_string())
    print("Email sent!")
