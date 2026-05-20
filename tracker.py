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

# 初始化資料檔案 (加入精算欄位：支付方式、回饋金額)
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

# 手機版專屬美化 CSS
st.markdown("""
    <style>
    .stApp { animation: fadeIn 0.5s ease-in-out; padding: 10px !important; }
    @keyframes fadeIn { 0% { opacity: 0; } 100% { opacity: 1; } }
    div.stButton > button { width: 100% !important; height: 48px !important; font-size: 16px !important; border-radius: 12px !important; }
    /* 讓分頁（Tabs）在手機上更大更直覺 */
    button[data-baseweb="tab"] { font-size: 16px !important; height: 50px !important; padding: 0px 16px !important; }
    .stProgress > div > div > div > div { background-image: linear-gradient(to right, #11998e 0%, #38ef7d 100%); height: 14px !important; }
    </style>
""", unsafe_allow_html=True)

# 載入資料
try:
    df = pd.read_csv(FILE_NAME, dtype={"日期": str}, encoding='utf-8-sig')
except:
    df = pd.DataFrame(columns=REQUIRED_COLUMNS)

# ================= 📱 手機 App 級頂部四大分頁 =================
tab_add, tab_budget, tab_chart, tab_excel = st.tabs(["✍️ 快速記帳", "🎯 預算回饋", "📈 數據盤點", "📋 帳目修正"])

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
        item_input = c_item.text_input("項目名稱 (如: 麥當勞)", "")
        
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
        # 精打細算亮點功能：紀錄回饋
        reward_input = c_reward.number_input("預估賺回饋/點數 ($)", min_value=0.0, step=0.1, format="%.1f") if type_input == "支出" else 0.0
        
        period_input = st.selectbox("帳目性質", ["單次消費", "每月固定", "每週固定"])
        
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
            st.success(f"✅ 已成功送出明細！")
            st.rerun()

# 💡 以下分頁需要有資料才運作
if not df.empty:
    calc_df = df.copy()
    calc_df['日期'] = pd.to_datetime(calc_df['日期'])
    calc_df['月份'] = calc_df['日期'].dt.strftime('%Y-%m')
    calc_df['金額'] = calc_df['金額'].astype(float)
    calc_df['回饋金額'] = calc_df['回饋金額'].astype(float)
    
    # 全域篩選，放在分頁最上方
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
        
        # 指標卡
        k1, k2 = st.columns(2)
        k1.metric(label="🟢 當月可支配收入", value=f"${total_income:,.0f}")
        k2.metric(label="🎁 已從小便宜賺回饋", value=f"${total_rewards:,.1f}")
        
        # 精算核心：倒數預算上限
        budget_limit = st.number_input("自訂本月「支出死線」($)", min_value=100.0, value=15000.0, step=500.0, format="%.0f")
        remaining_budget = budget_limit - total_expense
        
        if remaining_budget < 0:
            st.error(f"🚨 超支警告！你已經超花大洋 ${(abs(remaining_budget)):,.0f} 了！")
        else:
            st.metric(label="💰 本月剩餘可花預算 (重要！)", value=f"${remaining_budget:,.0f}")
            st.success(f"💪 優秀！預算還剩 {remaining_budget/budget_limit*100:.1f}%，請繼續保持。")
        
        st.progress(min(1.0, float(total_expense / budget_limit)))

    # ----------------- 分頁 3：多元數據盤點 -----------------
    with tab_chart:
        st.write("")
        st.subheader("📈 智慧財務視覺化")
        
        expense_df = filtered_calc[filtered_calc['類型'] == "支出"]
        sub_tab1, sub_tab2, sub_tab3 = st.tabs(["🏷️ 分類佔比", "📅 每日走勢", "💳 支付工具分析"])
        
        with sub_tab1:
            if not expense_df.empty:
                cate_chart = expense_df.groupby("類別")["金額"].sum().reset_index()
                st.plotly_chart(px.pie(cate_chart, values="金額", names="類別", hole=0.3, height=260), use_container_width=True)
            else: st.info("無支出數據")
            
        with sub_tab2:
            if not expense_df.empty:
                df_trend = expense_df.groupby(expense_df['日期'].dt.strftime('%Y-%m-%d'))["金額"].sum().reset_index()
                st.plotly_chart(px.line(df_trend, x="日期", y="金額", markers=True, line_shape="spline", height=260), use_container_width=True)
            else: st.info("無支出數據")
            
        with sub_tab3:
            if not expense_df.empty:
                st.write("#### 哪種支付工具刷最多？")
                pay_chart = expense_df.groupby("支付方式")["金額"].sum().reset_index()
                st.plotly_chart(px.bar(pay_chart, x="支付方式", y="金額", color="支付方式", height=260), use_container_width=True)
            else: st.info("無支出數據")

    # ----------------- 分頁 4：歷史明細修正 (Excel) -----------------
    with tab_excel:
        st.write("")
        st.subheader("📋 雲端對帳大表格")
        st.caption("💡 技巧：橫向滑動可改所有變數，改完數字點下方儲存，整行刪除點選最左邊按 Delete。")
        
        df['原始索引'] = df.index
        df_filtered_edit = df.copy()
        df_filtered_edit['臨時日期'] = pd.to_datetime(df_filtered_edit['日期'])
        df_filtered_edit['臨時月份'] = df_filtered_edit['臨時日期'].dt.strftime('%Y-%m')
        
        if selected_month != "全部月份":
            df_filtered_edit = df_filtered_edit[df_filtered_edit['臨時月份'] == selected_month]
        if selected_category != "全部類別":
            df_filtered_edit = df_filtered_edit[df_filtered_edit['類別'] == selected_category]
            
        df_filtered_edit = df_filtered_edit.drop(columns=['臨時日期', '臨時月份'])
        df_filtered_edit = df_filtered_edit.iloc[::-1].reset_index(drop=True)
        
        # 適合手機高頻率編輯、欄位高度對齊的 Excel 編輯器
        edited_df = st.data_editor(
            df_filtered_edit,
            column_config={
                "原始索引": None,
                "日期": st.column_config.TextColumn("日期"),
                "類型": st.column_config.SelectboxColumn("類型", options=["支出", "收入"], required=True),
                "項目": st.column_config.TextColumn("項目"),
                "類別": st.column_config.SelectboxColumn("類別", options=["飲食", "交通", "娛樂", "購物", "居住房租", "水電通訊", "醫療保健", "薪水", "獎金", "投資收益", "零用錢", "副業收入", "其他"]),
                "金額": st.column_config.NumberColumn("金額 ($)", min_value=0.0, format="$ %.0f"),
                "支付方式": st.column_config.SelectboxColumn("支付方式", options=["現金", "八達通", "PayMe/轉數快", "信用卡(賺回饋)", "銀行存款", "投資帳戶", "其他帳戶"]),
                "回饋金額": st.column_config.NumberColumn("回饋 ($)", min_value=0.0, format="$ %.1f"),
                "週期性": st.column_config.SelectboxColumn("性質", options=["單次消費", "每月固定", "每週固定"])
            },
            use_container_width=True,
            num_rows="dynamic",
            height=280
        )
        
        if st.button("💾 儲存所有對帳修改", type="primary", use_container_width=True):
            full_df = pd.read_csv(FILE_NAME, dtype={"日期": str}, encoding='utf-8-sig')
            for idx, row in edited_df.iterrows():
                orig_idx = row['原始索引']
                full_df.loc[orig_idx, REQUIRED_COLUMNS] = [row[c] for c in REQUIRED_COLUMNS]
                
            current_visible_orig_indices = edited_df['原始索引'].tolist()
            for orig_idx in df_filtered_edit['原始索引'].tolist():
                if orig_idx not in current_visible_orig_indices:
                    full_df = full_df.drop(orig_idx)
                    
            full_df.to_csv(FILE_NAME, index=False, encoding='utf-8-sig')
            st.success("🎉 雲端帳目已校對完畢！")
            st.rerun()
else:
    st.info("目前沒有紀錄，快新增第一筆吧！")
