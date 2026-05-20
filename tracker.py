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
st.set_page_config(page_title="精打細算神級記帳本", page_icon="📱", layout="centered")

# 手機版專屬美化 CSS（加入精美卡片樣式）
st.markdown("""
    <style>
    .stApp { animation: fadeIn 0.5s ease-in-out; padding: 10px !important; }
    @keyframes fadeIn { 0% { opacity: 0; } 100% { opacity: 1; } }
    div.stButton > button { width: 100% !important; height: 46px !important; font-size: 16px !important; border-radius: 12px !important; }
    button[data-baseweb="tab"] { font-size: 16px !important; height: 50px !important; padding: 0px 16px !important; }
    .stProgress > div > div > div > div { background-image: linear-gradient(to right, #11998e 0%, #38ef7d 100%); height: 14px !important; }
    
    /* 手機專用明細卡片樣式 */
    .expense-card {
        background-color: #f8f9fa;
        border-radius: 14px;
        padding: 15px;
        margin-bottom: 12px;
        border-left: 6px solid #e74c3c;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .income-card {
        background-color: #f8f9fa;
        border-radius: 14px;
        padding: 15px;
        margin-bottom: 12px;
        border-left: 6px solid #2ecc71;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

# 載入資料
try:
    df = pd.read_csv(FILE_NAME, dtype={"日期": str}, encoding='utf-8-sig')
except:
    df = pd.DataFrame(columns=REQUIRED_COLUMNS)

# ================= 📱 手機 App 級頂部四大分頁 =================
tab_add, tab_budget, tab_chart, tab_list = st.tabs(["✍️ 快速記帳", "🎯 預算回饋", "📈 數據盤點", "📋 歷史明細"])

# ----------------- 分頁 1：快速記帳 -----------------
with tab_add:
    st.write("")
    col_title, col_anim = st.columns([3, 1])
    col_title.subheader("⚡️ 單手秒速記帳")
    if lottie_wallet:
        with col_anim: st_lottie(lottie_wallet, speed=1, height=60, key="wallet_t1")

    with st.form(key='expense_form', clear_on_submit=True):
        type_input = st.radio("調整帳目類型", ["支出", "收入"], horizontal=True)
        
        c_date, c_item = st.columns(2)
        date_input = c_date.date_input("日期", datetime.now())
        item_input = c_item.text_input("項目名稱 (如: 午餐叉燒飯)", "")
        
        if type_input == "支出":
            categories = ["飲食", "交通", "娛樂", "購物", "居住房租", "水電通訊", "醫療保健", "其他"]
            pay_methods = ["現金", "八達通", "PayMe/轉數快", "信用卡(賺回饋)", "其他帳戶"]
        else:
            categories = ["薪水", "獎金", "投資收益", "零用錢", "副業收入", "其他"]
            pay_methods = ["銀行存款", "現金", "投資帳戶"]
            
        c_cat, c_amt = st.columns(2)
        category_input = c_cat.selectbox("項目類別", categories)
        amount_input = c_amt.number_input("金額 ($)", min_value=0.0, step=1.0, format="%.0f")
        
        c_pay, c_reward = st.columns(2)
        pay_input = c_pay.selectbox("支付/收款方式", pay_methods)
        reward_input = c_reward.number_input("預估賺回饋/點數 ($)", min_value=0.0, step=0.1, format="%.1f") if type_input == "支出" else 0.0
        
        period_input = st.selectbox("帳目性質", ["單次消費", "每月固定", "每週固定"])
        
        submit_button = st.form_submit_button(label='🚀 確定紀錄這一筆')

    if submit_button:
        if item_input.strip() == "":
            st.error("❌ 請輸入項目名稱！")
        elif amount_input <= 0:
            st.error("❌ 金額必須大於 0！")
        else:
            new_data = pd.DataFrame([[date_input.strftime("%Y-%m-%d"), type_input, item_input, category_input, amount_input, period_input, pay_input, reward_input]], 
                                    columns=REQUIRED_COLUMNS)
            new_data.to_csv(FILE_NAME, mode='a', header=False, index=False, encoding='utf-8-sig')
            st.success(f"✅ 已成功送出明細！")
            st.rerun()

# 💡 核心資料運作
if not df.empty:
    calc_df = df.copy()
    calc_df['日期'] = pd.to_datetime(calc_df['日期'])
    calc_df['月份'] = calc_df['日期'].dt.strftime('%Y-%m')
    calc_df['金額'] = calc_df['金額'].astype(float)
    calc_df['回饋金額'] = calc_df['回饋金額'].astype(float)
    
    # 全域篩選器 (維持手機大下拉選單樣式)
    st.write("---")
    c_f1, c_f2 = st.columns(2)
    selected_month = c_f1.selectbox("📅 篩選月份", ["全部月份"] + sorted(calc_df['月份'].unique().tolist(), reverse=True))
    selected_category = c_f2.selectbox("🏷️ 篩選類別", ["全部類別"] + sorted(calc_df['類別'].dropna().unique().tolist()))
    
    filtered_calc = calc_df.copy()
    if selected_month != "全部月份":
        filtered_calc = filtered_calc[filtered_calc['月份'] == selected_month]
    if selected_category != "全部類別":
        filtered_calc = filtered_calc[filtered_calc['類別'] == selected_category]
        
    total_income = filtered_calc[filtered_calc['類型'] == "收入"]['金額'].sum()
    total_expense = filtered_calc[filtered_calc['類型'] == "支出"]['金額'].sum()
    total_rewards = filtered_calc[filtered_calc['類型'] == "支出"]['回饋金額'].sum()
    balance = total_income - total_expense

    # ----------------- 分頁 2：預算與回饋控管 -----------------
    with tab_budget:
        st.write("")
        st.subheader("🎯 精打細算控制台")
        
        k1, k2 = st.columns(2)
        k1.metric(label="🟢 當月可支配收入", value=f"${total_income:,.0f}")
        k2.metric(label="🎁 已從小便宜賺回饋", value=f"${total_rewards:,.1f}")
        
        budget_limit = st.number_input("自訂本月「支出死線」($)", min_value=100.0, value=15000.0, step=500.0, format="%.0f")
        remaining_budget = budget_limit - total_expense
        
        if remaining_budget < 0:
            st.error(f"🚨 超支警告！你已經超花大洋 ${(abs(remaining_budget)):,.0f} 了！")
        else:
            st.metric(label="💰 本月剩餘可花預算", value=f"${remaining_budget:,.0f}")
            st.success(f"💪 預算還剩 {remaining_budget/budget_limit*100:.1f}%")
        
        st.progress(min(1.0, float(total_expense / budget_limit)))

    # ----------------- 分頁 3：多元數據盤點 -----------------
    with tab_chart:
        st.write("")
        st.subheader("📈 智慧財務視覺化")
        expense_df = filtered_calc[filtered_calc['類型'] == "支出"]
        sub_tab1, sub_tab2, sub_tab3 = st.tabs(["🏷️ 分類佔比", "📅 每日走勢", "💳 支付工具"])
        
        with sub_tab1:
            if not expense_df.empty:
                cate_chart = expense_df.groupby("類別")["金額"].sum().reset_index()
                st.plotly_chart(px.pie(cate_chart, values="金額", names="類別", hole=0.3, height=250), use_container_width=True)
            else: st.info("無支出數據")
            
        with sub_tab2:
            if not expense_df.empty:
                df_trend = expense_df.groupby(expense_df['日期'].dt.strftime('%Y-%m-%d'))["金額"].sum().reset_index()
                st.plotly_chart(px.line(df_trend, x="日期", y="金額", markers=True, line_shape="spline", height=250), use_container_width=True)
            else: st.info("無支出數據")
            
        with sub_tab3:
            if not expense_df.empty:
                pay_chart = expense_df.groupby("支付方式")["金額"].sum().reset_index()
                st.plotly_chart(px.bar(pay_chart, x="支付方式", y="金額", color="支付方式", height=250), use_container_width=True)
            else: st.info("無支出數據")

    # ----------------- 🔥 分頁 4：手機極致優化！卡片式歷史明細與修改 -----------------
    with tab_list:
        st.write("")
        st.subheader("📋 歷史帳目卡片清單")
        st.caption("💡 專為手機設計：免左右滑動！點擊卡片下方的按鈕即可直接修改變數或刪除。")
        
        # 綁定原始索引
        df['原始索引'] = df.index
        
        # 依據篩選條件過濾要顯示的卡片
        df_display = df.copy()
        df_display['臨時日期'] = pd.to_datetime(df_display['日期'])
        df_display['臨時月份'] = df_display['臨時日期'].dt.strftime('%Y-%m')
        
        if selected_month != "全部月份":
            df_display = df_display[df_display['臨時月份'] == selected_month]
        if selected_category != "全部類別":
            df_display = df_display[df_display['類別'] == selected_category]
            
        df_display = df_display.drop(columns=['臨時日期', '臨時月份'])
        # 倒序排列，讓最新消費在最上面
        df_display = df_display.iloc[::-1]
        
        if df_display.empty:
            st.info("當前篩選條件下沒有帳目紀錄。")
        else:
            for idx, row in df_display.iterrows():
                orig_idx = int(row['原始索引'])
                card_style = "expense-card" if row['類型'] == "支出" else "income-card"
                icon = "🔴" if row['類型'] == "支出" else "🟢"
                
                # 渲染手機版漂亮卡片
                reward_text = f" | 🎁 回饋: ${row['回饋金額']}" if row['類型'] == "支出" and float(row['回饋金額']) > 0 else ""
                st.markdown(f"""
                <div class="{card_style}">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-size: 14px; color: #7f8c8d;">📅 {row['日期']} ({row['週期性']})</span>
                        <span style="font-size: 20px; font-weight: bold; color: #2c3e50;">${float(row['金額']):,.0f}</span>
                    </div>
                    <div style="margin-top: 8px; font-size: 16px; font-weight: 500;">
                        {icon} {row['項目']} <span style="font-size: 13px; color: #95a5a6; background: #eaeaea; padding: 2px 6px; border-radius: 6px; margin-left: 5px;">{row['類別']}</span>
                    </div>
                    <div style="margin-top: 5px; font-size: 13px; color: #7f8c8d;">
                        💳 支付: {row['支付方式']}{reward_text}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # 卡片附帶大功能按鈕 (修改與刪除)
                btn_col1, btn_col2 = st.columns(2)
                
                # 點擊「✏️ 修改」會就地展開一個專屬的獨立大表單
                with btn_col1:
                    edit_clicked = st.checkbox(f"✏️ 修改此筆", key=f"click_edit_{orig_idx}")
                with btn_col2:
                    if st.button("🗑️ 刪除", key=f"click_del_{orig_idx}"):
                        full_df = pd.read_csv(FILE_NAME, dtype={"日期": str}, encoding='utf-8-sig')
                        full_df = full_df.drop(orig_idx)
                        full_df.to_csv(FILE_NAME, index=False, encoding='utf-8-sig')
                        st.success("已成功刪除該筆紀錄！")
                        st.rerun()
                
                # 如果使用者勾選了修改，彈出手機大尺寸輸入表單
                if edit_clicked:
                    st.info(f"正在修改：{row['項目']}")
                    with st.form(key=f"edit_form_{orig_idx}"):
                        new_type = st.radio("類型", ["支出", "收入"], index=0 if row['類型']=="支出" else 1, horizontal=True, key=f"edit_type_{orig_idx}")
                        new_date = st.date_input("日期", datetime.strptime(row['日期'], "%Y-%m-%d"), key=f"edit_date_{orig_idx}")
                        new_item = st.text_input("項目名稱", value=row['項目'], key=f"edit_item_{orig_idx}")
                        
                        all_cats = ["飲食", "交通", "娛樂", "購物", "居住房租", "水電通訊", "醫療保健", "薪水", "獎金", "投資收益", "零用錢", "副業收入", "其他"]
                        current_cat_idx = all_cats.index(row['類別']) if row['類別'] in all_cats else 0
                        new_cat = st.selectbox("類別", all_cats, index=current_cat_idx, key=f"edit_cat_{orig_idx}")
                        
                        new_amt = st.number_input("金額 ($)", min_value=0.0, value=float(row['金額']), step=1.0, format="%.0f", key=f"edit_amt_{orig_idx}")
                        
                        all_pays = ["現金", "八達通", "PayMe/轉數快", "信用卡(賺回饋)", "銀行存款", "投資帳戶", "其他帳戶"]
                        current_pay_idx = all_pays.index(row['支付方式']) if row['支付方式'] in all_pays else 0
                        new_pay = st.selectbox("支付/收款方式", all_pays, index=current_pay_idx, key=f"edit_pay_{orig_idx}")
                        
                        new_reward = st.number_input("回饋金額 ($)", min_value=0.0, value=float(row['回饋金額']), step=0.1, format="%.1f", key=f"edit_rew_{orig_idx}")
                        new_period = st.selectbox("帳目性質", ["單次消費", "每月固定", "每週固定"], index=["單次消費", "每月固定", "每週固定"].index(row['週期性']), key=f"edit_per_{orig_idx}")
                        
                        save_submit = st.form_submit_button("💾 儲存此筆變更")
                        
                        if save_submit:
                            full_df = pd.read_csv(FILE_NAME, dtype={"日期": str}, encoding='utf-8-sig')
                            full_df.loc[orig_idx, REQUIRED_COLUMNS] = [
                                new_date.strftime("%Y-%m-%d"), new_type, new_item, new_cat, new_amt, new_period, new_pay, new_reward
                            ]
                            full_df.to_csv(FILE_NAME, index=False, encoding='utf-8-sig')
                            st.success("修改成功！")
                            st.rerun()
                st.write("") # 卡片之間的間距
else:
    st.info("目前沒有紀錄，快新增第一筆吧！")
