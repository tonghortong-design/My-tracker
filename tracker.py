import streamlit as st
import pandas as pd
import os
import plotly.express as px
from datetime import datetime
import requests
from streamlit_lottie import st_lottie

FILE_NAME = "expense_tracker.csv"

def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

lottie_wallet = load_lottieurl("https://assets5.lottiefiles.com/packages/lf20_y9m8vtas.json")

# 初始化資料檔案
REQUIRED_COLUMNS = ["日期", "類型", "項目", "類別", "金額", "週期性", "支付方式", "回饋金額"]
if not os.path.exists(FILE_NAME):
    df = pd.DataFrame(columns=REQUIRED_COLUMNS)
    df.to_csv(FILE_NAME, index=False, encoding='utf-8-sig')
else:
    df_check = pd.read_csv(FILE_NAME, encoding='utf-8-sig')
    updated = False
    for col in REQUIRED_COLUMNS:
        if col not in df_check.columns:
            df_check[col] = 0 if col == "回饋金額" else ("現金" if col == "支付方式" else "單次消費")
            updated = True
    if updated:
        df_check.to_csv(FILE_NAME, index=False, encoding='utf-8-sig')

# 網頁配置
st.set_page_config(page_title="天天記帳 App", page_icon="💰", layout="centered")

# 優化手機端與視覺體驗的極簡 CSS
st.markdown("""
    <style>
    .stApp { animation: fadeIn 0.4s ease-in-out; padding: 12px !important; }
    @keyframes fadeIn { 0% { opacity: 0; } 100% { opacity: 1; } }
    div.stButton > button { width: 100% !important; height: 50px !important; font-size: 18px !important; font-weight: bold; border-radius: 14px !important; background: linear-gradient(135deg, #4285F4 0%, #34A853 100%) !important; color: white !important; border: none !important; }
    button[data-baseweb="tab"] { font-size: 16px !important; height: 45px !important; }
    .stProgress > div > div > div > div { background-image: linear-gradient(to right, #11998e 0%, #38ef7d 100%); height: 10px !important; }
    
    /* 卡片美化：正常人最愛的清爽扁平風 */
    .expense-card { background-color: #ffffff; border-radius: 12px; padding: 14px; margin-bottom: 10px; border-left: 5px solid #ea4335; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    .income-card { background-color: #ffffff; border-radius: 12px; padding: 14px; margin-bottom: 10px; border-left: 5px solid #34a853; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    </style>
""", unsafe_allow_html=True)

try:
    df = pd.read_csv(FILE_NAME, dtype={"日期": str}, encoding='utf-8-sig')
except:
    df = pd.DataFrame(columns=REQUIRED_COLUMNS)

# 頂部迎賓標題
col_title, col_anim = st.columns([3, 1])
with col_title:
    st.title("💰 我的天天記帳本")
    st.caption("✨ 簡單、直覺、單手 3 秒完成記帳")
with col_anim:
    if lottie_wallet: st_lottie(lottie_wallet, speed=1, height=65, key="wallet_top")

# ================= 預先計算全域財務數據 =================
if not df.empty:
    calc_df = df.copy()
    calc_df['日期'] = pd.to_datetime(calc_df['日期'])
    calc_df['月份'] = calc_df['日期'].dt.strftime('%Y-%m')
    calc_df['金額'] = calc_df['金額'].astype(float)
    calc_df['回饋金額'] = calc_df['回饋金額'].astype(float)
    
    current_month_str = datetime.now().strftime('%Y-%m')
    if current_month_str not in calc_df['月份'].values:
        current_month_str = calc_df['月份'].iloc[-1] if not calc_df['月份'].empty else "全部"
else:
    current_month_str = "全部"

# ================= 📱 頂部三大手機分頁 =================
tab_add, tab_chart, tab_list = st.tabs(["✍️ 快速記帳", "🎯 預算看板", "📋 歷史明細"])

# ----------------- 分頁 1：無腦快速記帳 -----------------
with tab_add:
    st.write("")
    with st.form(key='expense_form', clear_on_submit=True):
        type_input = st.radio("調整帳目類型", ["支出", "收入"], horizontal=True)
        
        # 正常人最關心的核心欄位
        item_input = st.text_input("📝 項目名稱 (例如: 午餐、薪水)", "")
        amount_input = st.number_input("💰 金額 ($)", min_value=0.0, step=1.0, format="%.0f")
        
        # 預設分類
        if type_input == "支出":
            categories = ["飲食", "交通", "娛樂", "購物", "居住房租", "水電通訊", "其他"]
            pay_methods = ["現金", "八達通", "PayMe/轉數快", "信用卡(賺回饋)", "其他帳戶"]
        else:
            categories = ["薪水", "獎金", "投資收益", "零用錢", "其他"]
            pay_methods = ["銀行存款", "現金"]
            
        c_cat, c_date = st.columns(2)
        category_input = c_cat.selectbox("🏷️ 類別", categories)
        date_input = c_date.date_input("📅 日期", datetime.now())
        
        # 🔥 修正亮點：把精打細算、重複週期等複雜功能藏在摺疊選單內！普通人可以直接無視！
        with st.expander("🔍 進階精算設定 (選填欄位)"):
            pay_input = st.selectbox("卡片/支付方式", pay_methods, index=0)
            reward_input = st.number_input("預估賺回饋金/點數 ($)", min_value=0.0, step=1.0, format="%.0f") if type_input == "支出" else 0.0
            period_input = st.selectbox("重複週期", ["單次消費", "每月固定", "每週固定"])
            
        # 正常的預設值補齊
        if 'pay_input' not in locals(): pay_input = "現金"
        if 'reward_input' not in locals(): reward_input = 0.0
        if 'period_input' not in locals(): period_input = "單次消費"
        
        # 超大、超好按的手機按鈕
        submit_button = st.form_submit_button(label='🚀 紀錄這一筆')

    if submit_button:
        if item_input.strip() == "":
            st.error("❌ 請輸入項目名稱！")
        elif amount_input <= 0:
            st.error("❌ 金額必須大於 0！")
        else:
            new_data = pd.DataFrame([[date_input.strftime("%Y-%m-%d"), type_input, item_input, category_input, amount_input, period_input, pay_input, reward_input]], 
                                    columns=REQUIRED_COLUMNS)
            new_data.to_csv(FILE_NAME, mode='a', header=False, index=False, encoding='utf-8-sig')
            st.success(f"✅ 成功記錄：{item_input} ${amount_input:.0f}！")
            st.rerun()

# ----------------- 分頁 2：簡單易懂的預算與圖表 -----------------
with tab_chart:
    if not df.empty:
        st.write("")
        st.subheader("🎯 本月財務控管中心")
        
        # 篩選月份切換
        selected_month = st.selectbox("📅 切換查看月份：", sorted(calc_df['月份'].unique().tolist(), reverse=True), index=0)
        
        m_calc = calc_df[calc_df['月份'] == selected_month]
        m_income = m_calc[m_calc['類型'] == "收入"]['金額'].sum()
        m_expense = m_calc[m_calc['類型'] == "支出"]['金額'].sum()
        m_rewards = m_calc[m_calc['類型'] == "支出"]['回饋金額'].sum()
        
        # 大字體、無小數點的簡潔看版
        k1, k2 = st.columns(2)
        k1.metric(label="🟢 本月總收入", value=f"${m_income:,.0f}")
        k2.metric(label="🔴 本月總支出", value=f"${m_expense:,.0f}")
        
        # 正常人最想看的「剩餘預算」
        budget_limit = st.number_input("設定每月花費死線 ($)", min_value=100.0, value=15000.0, step=1000.0, format="%.0f")
        rem_budget = budget_limit - m_expense
        
        if rem_budget < 0:
            st.error(f"🚨 警告：本月已超支 ${abs(rem_budget):,.0f}！要省錢了！")
        else:
            st.metric(label="💰 本月剩餘可用額度", value=f"${rem_budget:,.0f}")
            if m_rewards > 0:
                st.caption(f"🎁 小確幸：本月透過刷卡/活動額外賺回了 ${m_rewards:,.0f} 的回饋！")
        st.progress(min(1.0, float(m_expense / budget_limit)))
        
        # 簡單圖表
        st.write("---")
        st.write("#### 📊 錢都花到哪去了？")
        m_exp_df = m_calc[m_calc['類型'] == "支出"]
        if not m_exp_df.empty:
            cate_chart = m_exp_df.groupby("類別")["金額"].sum().reset_index()
            st.plotly_chart(px.pie(cate_chart, values="金額", names="類別", hole=0.4, height=260), use_container_width=True)
        else:
            st.info("本月尚無支出紀錄。")
    else:
        st.info("暫無資料。")

# ----------------- 分頁 3：手機卡片式明細與單擊修改 -----------------
with tab_list:
    if not df.empty:
        st.write("")
        st.subheader("📋 歷史帳目清單")
        
        df['原始索引'] = df.index
        # 明細頁面的快速類別篩選，維持簡潔
        history_month = st.selectbox("選擇對帳月份", ["全部"] + sorted(calc_df['月份'].unique().tolist(), reverse=True), key="hist_month")
        
        df_display = df.copy()
        if history_month != "全部":
            df_display['臨時日期'] = pd.to_datetime(df_display['日期'])
            df_display = df_display[df_display['臨時日期'].dt.strftime('%Y-%m') == history_month].drop(columns=['臨時日期'])
            
        df_display = df_display.iloc[::-1] # 最新在最前
        
        if df_display.empty:
            st.info("沒有找到任何帳目。")
        else:
            for idx, row in df_display.iterrows():
                orig_idx = int(row['原始索引'])
                card_style = "expense-card" if row['類型'] == "支出" else "income-card"
                icon = "🔴" if row['類型'] == "支出" else "🟢"
                
                # 簡潔的手機卡片渲染
                st.markdown(f"""
                <div class="{card_style}">
                    <div style="display: flex; justify-content: space-between;">
                        <span style="font-size: 13px; color: #888;">📅 {row['日期']}</span>
                        <span style="font-size: 18px; font-weight: bold;">${float(row['金額']):,.0f}</span>
                    </div>
                    <div style="margin-top: 6px; font-size: 16px;">
                        {icon} <b>{row['項目']}</b> <span style="font-size: 12px; color: #666; background: #eee; padding: 2px 6px; border-radius: 4px; margin-left: 4px;">{row['類別']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # 手機好點擊的大按鈕
                b1, b2 = st.columns(2)
                edit_active = b1.checkbox("✏️ 快速改", key=f"active_mod_{orig_idx}")
                if b2.button("🗑️ 刪除", key=f"card_delete_{orig_idx}"):
                    full_df = pd.read_csv(FILE_NAME, dtype={"日期": str}, encoding='utf-8-sig')
                    full_df = full_df.drop(orig_idx)
                    full_df.to_csv(FILE_NAME, index=False, encoding='utf-8-sig')
                    st.success("已成功移除該筆紀錄！")
                    st.rerun()
                    
                if edit_active:
                    with st.form(key=f"fast_mod_form_{orig_idx}"):
                        st.caption("📱 正在修改這筆資料")
                        m_item = st.text_input("項目名稱", value=row['項目'], key=f"m_it_{orig_idx}")
                        m_amt = st.number_input("金額 ($)", min_value=0.0, value=float(row['金額']), format="%.0f", key=f"m_am_{orig_idx}")
                        
                        all_cats = ["飲食", "交通", "娛樂", "購物", "居住房租", "水電通訊", "其他"]
                        c_idx = all_cats.index(row['類別']) if row['類別'] in all_cats else 0
                        m_cat = st.selectbox("類別", all_cats, index=c_idx, key=f"m_ca_{orig_idx}")
                        
                        save_btn = st.form_submit_button("💾 完成修改")
                        if save_btn:
                            full_df = pd.read_csv(FILE_NAME, dtype={"日期": str}, encoding='utf-8-sig')
                            full_df.loc[orig_idx, ["項目", "金額", "類別"]] = [m_item, m_amt, m_cat]
                            full_df.to_csv(FILE_NAME, index=False, encoding='utf-8-sig')
                            st.success("修改成功！")
                            st.rerun()
                st.write("")
    else:
        st.info("快去第一頁新增帳目吧！")
