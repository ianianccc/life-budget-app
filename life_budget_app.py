"""
生活費管家 App — 專為 30-65 歲設計
功能：
  1. 首頁顯示本月剩餘預算 & 今日可花費
  2. 必要 / 想要 / 固定 三分類記帳
  3. 手機友善大字體
  4. 智慧鼓勵提醒
  5. 固定金額法說明
  6. 週報生成器
"""

import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, date, timedelta
import calendar

# ── 頁面設定 ──────────────────────────────────────────────
st.set_page_config(
    page_title="生活費管家 💰",
    page_icon="💰",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── 全域 CSS（手機友善大字體）────────────────────────────
st.markdown("""
<style>
  /* 全站字體放大，30-65 歲閱讀無壓力 */
  html, body, [class*="css"] { font-size: 18px !important; }

  .big-number {
      font-size: 2.6rem;
      font-weight: 800;
      text-align: center;
      line-height: 1.2;
  }
  .green  { color: #27ae60; }
  .orange { color: #e67e22; }
  .red    { color: #e74c3c; }
  .grey   { color: #7f8c8d; }

  .card {
      background: #f9f9f9;
      border-radius: 16px;
      padding: 1.2rem 1.4rem;
      margin-bottom: 1rem;
      box-shadow: 0 2px 8px rgba(0,0,0,.07);
  }
  .reminder-box {
      background: linear-gradient(135deg,#667eea,#764ba2);
      color: white;
      border-radius: 14px;
      padding: 1rem 1.4rem;
      font-size: 1.25rem;
      text-align: center;
      margin: 0.8rem 0 1.2rem;
  }
  .weekly-box {
      background: linear-gradient(135deg,#f093fb,#f5576c);
      color: white;
      border-radius: 14px;
      padding: 1rem 1.4rem;
      font-size: 1.15rem;
      margin-top: 0.6rem;
  }
  /* 按鈕放大 */
  div.stButton > button {
      font-size: 1.3rem !important;
      padding: 0.7rem 1rem !important;
      border-radius: 12px !important;
      width: 100% !important;
      min-height: 3.2rem !important;
  }
  div.stNumberInput input {
      font-size: 1.3rem !important;
  }
  div.stTextInput input {
      font-size: 1.15rem !important;
  }
  hr { margin: 1.2rem 0; }
</style>
""", unsafe_allow_html=True)

# ── 資料持久化（JSON 存在本地，重啟不遺失）────────────────
DATA_FILE = os.path.join(os.path.dirname(__file__), "budget_data.json")

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "monthly_budget": 0,
        "expenses": []          # {date, category, amount, note}
    }

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ── 載入資料到 session_state ──────────────────────────────
if "data" not in st.session_state:
    st.session_state.data = load_data()

data = st.session_state.data

# ── 工具函式 ──────────────────────────────────────────────
def this_month_expenses():
    today = date.today()
    return [
        e for e in data["expenses"]
        if e["date"].startswith(f"{today.year}-{today.month:02d}")
    ]

def today_expenses():
    today_str = date.today().isoformat()
    return [e for e in data["expenses"] if e["date"] == today_str]

def calc_remaining():
    spent = sum(e["amount"] for e in this_month_expenses())
    return data["monthly_budget"] - spent

def calc_daily_budget(remaining):
    today = date.today()
    days_left = calendar.monthrange(today.year, today.month)[1] - today.day + 1
    return remaining / days_left if days_left > 0 else 0

def reminder_message(remaining, monthly_budget):
    if monthly_budget == 0:
        return "📌 請先設定本月生活費預算！"
    ratio = remaining / monthly_budget
    if ratio > 0.6:
        return "🌟 生活辛苦了，對自己好一點！"
    elif ratio > 0.35:
        return "👍 節奏不錯，繼續保持均衡生活！"
    elif ratio > 0.15:
        return "⚡ 再堅持一下，月底就快到了。"
    elif ratio > 0:
        return "💪 最後衝刺！省下的都是你的！"
    else:
        return "🚨 本月預算已超標，下個月重新出發！"

def color_class(remaining, monthly_budget):
    if monthly_budget == 0:
        return "grey"
    ratio = remaining / monthly_budget
    if ratio > 0.35:
        return "green"
    elif ratio > 0.1:
        return "orange"
    else:
        return "red"

def week_range():
    today = date.today()
    start = today - timedelta(days=today.weekday() + 1)  # 上週日
    if today.weekday() == 6:                              # 今天是週日
        start = today - timedelta(days=6)
    end = start + timedelta(days=6)
    return start, end

def weekly_expenses():
    start, end = week_range()
    return [
        e for e in data["expenses"]
        if start.isoformat() <= e["date"] <= end.isoformat()
    ]

def generate_weekly_report():
    items = weekly_expenses()
    if not items:
        return "這週還沒有記帳記錄，從今天開始養成習慣吧！💡"
    df = pd.DataFrame(items)
    total = df["amount"].sum()
    by_cat = df.groupby("category")["amount"].sum().sort_values(ascending=False)
    top_cat = by_cat.index[0]
    top_amt = by_cat.iloc[0]
    cat_pct = int(top_amt / total * 100)
    start, end = week_range()

    lines = [
        f"📊 **{start.strftime('%m/%d')} ~ {end.strftime('%m/%d')} 週報**",
        f"",
        f"本週共花費 **NT${total:,.0f}**，",
        f"其中「{top_cat}」佔最多（{cat_pct}%，NT${top_amt:,.0f}）。",
        f"",
    ]
    for cat in ["必要", "想要", "固定"]:
        amt = by_cat.get(cat, 0)
        lines.append(f"• {cat}：NT${amt:,.0f}")
    lines.append("")

    # 一句話總結
    if by_cat.get("想要", 0) > by_cat.get("必要", 0):
        lines.append("✨ 這週享受了不少生活，下週可以更節制一點哦！")
    elif by_cat.get("必要", 0) / total > 0.7:
        lines.append("💼 這週幾乎都是必要開銷，辛苦了！")
    else:
        lines.append("✅ 這週支出結構均衡，繼續維持！")
    return "\n".join(lines)

# ══════════════════════════════════════════════════════════
#  UI 開始
# ══════════════════════════════════════════════════════════

st.title("💰 生活費管家")
st.caption(f"📅 {date.today().strftime('%Y 年 %m 月 %d 日')}")

# ── ① 設定預算（折疊區塊）────────────────────────────────
with st.expander("⚙️ 設定本月生活費預算", expanded=(data["monthly_budget"] == 0)):
    st.markdown("""
    <div style='font-size:1.05rem; color:#555; margin-bottom:0.6rem;'>
    💡 <b>固定金額法建議</b>：每月初將生活費單獨匯入一個帳戶（或領出現金），
    App 的數字只跟這筆錢連動，不混入儲蓄或投資，壓力最輕。
    </div>
    """, unsafe_allow_html=True)

    new_budget = st.number_input(
        "本月生活費（NT$）",
        min_value=0,
        max_value=500000,
        value=int(data["monthly_budget"]),
        step=1000,
        format="%d",
    )
    if st.button("💾 儲存預算"):
        data["monthly_budget"] = new_budget
        save_data(data)
        st.success(f"✅ 本月預算設定為 NT${new_budget:,}")
        st.rerun()

st.markdown("---")

# ── ② 首頁核心數字 ────────────────────────────────────────
remaining   = calc_remaining()
daily_allow = calc_daily_budget(remaining)
cc = color_class(remaining, data["monthly_budget"])

col1, col2 = st.columns(2)
with col1:
    st.markdown(f"""
    <div class='card'>
      <div style='text-align:center; font-size:1rem; color:#888; margin-bottom:4px;'>
        本月剩餘預算
      </div>
      <div class='big-number {cc}'>
        NT${remaining:,.0f}
      </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class='card'>
      <div style='text-align:center; font-size:1rem; color:#888; margin-bottom:4px;'>
        今日可花費
      </div>
      <div class='big-number {'green' if daily_allow > 0 else 'red'}'>
        NT${max(daily_allow,0):,.0f}
      </div>
    </div>
    """, unsafe_allow_html=True)

# ── 鼓勵提醒 ─────────────────────────────────────────────
st.markdown(f"""
<div class='reminder-box'>
  {reminder_message(remaining, data["monthly_budget"])}
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ── ③ 記帳區 ─────────────────────────────────────────────
st.subheader("📝 新增一筆支出")

amount = st.number_input(
    "金額（NT$）",
    min_value=0,
    max_value=100000,
    value=0,
    step=10,
    format="%d",
    key="input_amount",
)
note = st.text_input("備註（選填）", placeholder="例：午餐、停車費…", key="input_note")

col_a, col_b, col_c = st.columns(3)

CATEGORY_ICONS = {"必要": "🍚", "想要": "🛍️", "固定": "🏠"}

def add_expense(category):
    amt = st.session_state.input_amount
    if amt <= 0:
        st.warning("請先輸入金額！")
        return
    entry = {
        "date": date.today().isoformat(),
        "category": category,
        "amount": amt,
        "note": st.session_state.input_note,
    }
    data["expenses"].append(entry)
    save_data(data)
    # 計算最新剩餘後更新提示
    new_remaining = calc_remaining()
    st.session_state["last_reminder"] = reminder_message(new_remaining, data["monthly_budget"])
    st.session_state["last_entry"] = f"{CATEGORY_ICONS[category]} {category} NT${amt:,}"
    st.rerun()

with col_a:
    if st.button("🍚\n必要"):
        add_expense("必要")
with col_b:
    if st.button("🛍️\n想要"):
        add_expense("想要")
with col_c:
    if st.button("🏠\n固定"):
        add_expense("固定")

# 記帳後提示
if "last_entry" in st.session_state:
    st.success(f"✅ 已記錄 {st.session_state['last_entry']}")
    st.markdown(f"""
    <div class='reminder-box' style='margin-top:0.4rem;'>
      {st.session_state.get('last_reminder','')}
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ── ④ 今日明細 ────────────────────────────────────────────
st.subheader("📋 今日明細")
today_items = today_expenses()
if today_items:
    df_today = pd.DataFrame(today_items)[["category","amount","note"]]
    df_today.columns = ["分類", "金額(NT$)", "備註"]
    df_today["金額(NT$)"] = df_today["金額(NT$)"].map("{:,.0f}".format)
    st.dataframe(df_today, use_container_width=True, hide_index=True)
    st.caption(f"今日合計：NT${sum(e['amount'] for e in today_items):,}")
else:
    st.info("今天還沒有記帳紀錄。")

st.markdown("---")

# ── ⑤ 本月分類圖 ─────────────────────────────────────────
st.subheader("📊 本月支出分佈")
month_items = this_month_expenses()
if month_items:
    df_month = pd.DataFrame(month_items)
    by_cat = df_month.groupby("category")["amount"].sum().reset_index()
    by_cat.columns = ["分類", "金額"]
    st.bar_chart(by_cat.set_index("分類"), use_container_width=True, color="#764ba2")
    total_spent = df_month["amount"].sum()
    st.caption(
        f"本月已花費 NT${total_spent:,.0f} ／ 預算 NT${data['monthly_budget']:,.0f}"
    )
else:
    st.info("本月尚無支出記錄。")

st.markdown("---")

# ── ⑥ 週報生成器 ─────────────────────────────────────────
st.subheader("📅 週報生成器")
st.caption("每週日晚上點一下，看看這週花最多的是什麼。")

if st.button("🔍 生成本週報告"):
    report = generate_weekly_report()
    st.markdown(f"""
    <div class='weekly-box'>
      {report.replace(chr(10), '<br>')}
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ── ⑦ 資料管理 ───────────────────────────────────────────
with st.expander("🗂️ 資料管理"):
    st.caption("匯出或清除資料（清除後無法復原）")
    col_x, col_y = st.columns(2)
    with col_x:
        if month_items:
            df_export = pd.DataFrame(month_items)
            csv = df_export.to_csv(index=False, encoding="utf-8-sig")
            st.download_button(
                "⬇️ 匯出本月 CSV",
                data=csv,
                file_name=f"budget_{date.today().strftime('%Y%m')}.csv",
                mime="text/csv",
            )
    with col_y:
        if st.button("🗑️ 清除本月資料"):
            today = date.today()
            prefix = f"{today.year}-{today.month:02d}"
            data["expenses"] = [e for e in data["expenses"] if not e["date"].startswith(prefix)]
            save_data(data)
            st.session_state.pop("last_entry", None)
            st.success("本月資料已清除。")
            st.rerun()
