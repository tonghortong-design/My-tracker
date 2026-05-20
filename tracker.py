import streamlit as st
import pandas as pd
import os
import plotly.express as px
from datetime import datetime
import requests
from streamlit_lottie import st_lottie

FILE_NAME = "expense_tracker.csv"

# 載入 Lottie 動畫
def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

lottie_wallet = load_lottieurl("https://assets5.lottiefiles.com/packages/lf20_y9m8vtas.json")

# 初始化資料檔案
if not os.path.exists(FILE_NAME):
    df = pd.DataFrame(columns=["日期", "類型", "項目", "類別", "金額", "週期性"])
    df.to_csv(FILE_NAME, index=False, encoding='utf-8-sig')
else:
    df_check = pd.read_csv(FILE_NAME, encoding='utf-8-sig')
    if "類型" not in df_check.columns:
        df_check.insert(1, "類型", "支出")
    if "週期性" not in df_check.columns:
        df_check["週期性"] = "單次消費"
    df_check.to_csv(FILE_NAME, index=False, encoding='utf-8-sig')

# 網頁配置（手機版高度優化）
st.set_page_config(page_title="天天記帳本", page_icon="📱", layout="centered")

# 注入手機專屬 UI 優化 CSS
st.markdown("""
    <style>
    /* 讓整個網頁有 App 的淡入感 */
    .stApp {
        animation: fadeIn 0.8s ease-in-out;
        padding: 10px !important;
    }
    @keyframes fadeIn {
        0% { opacity: 0; transform: translateY(5px); }
        100% { opacity: 1; transform: translateY(0); }
    }
    /* 加大手機按鈕點擊區域，全面變成大按鈕 */
    div.stButton > button {
        width: 100% !important;
        height: 50px !important;
        font-size: 18px !important;
        border-radius: 12px !important;
        margin-top: 10px;
    }
    /* 優化手機單選按鈕 (Radio) 的間距 */
    div[data-testid="stMarkdownContainer"] p {
        font-size: 16px;
    }
    /* 調整進度條高度與顏色 */
    .stProgress > div > div > div > div {
        background-image: linear-gradient(to right, #4facfe 0%, #00f2fe 100%);
        height: 12px !important;
    }
    </style>
""", unsafe_allow_html=True)

# 頂部標題區
col_title, col_anim = st.columns([3, 1])
with col_title:
    st.title("📱 天天記帳本")
    st.caption("✨ 已啟用手機單手操作優化介面")
with col_anim:
    if lottie_wallet:
        st_lottie(lottie_wallet, speed=1, height=70, key="wallet")

# ================= 🔥 手機優化：直接在畫面上方快速記帳 =================
with st.expander("✍️ 點擊展開・快速記帳功能", expanded=True):
    with st.form(key='expense_form', clear_on_submit=True):
        type_input = st.radio("調整類型", ["支出", "收入"], horizontal=True)
        
        # 讓日期、項目排緊湊一點
        c_date, c_item = st.columns(2)
        date_input = c_date.date_input("日期", datetime.now())
        item_input = c_item.text_input("項目名稱 (如: 午餐)", "")
        
        if type_input == "支出":
            categories = ["飲食", "交通", "娛樂", "購物", "居住房租", "水電通訊", "醫療保健", "其他"]
        else:
            categories = ["薪水", "獎金", "投資收益", "零用錢", "副業收入", "其他"]
            
        c_cat, c_amt = st.columns(2)
        category_input = c_cat.selectbox("項目類別", categories)
        amount_input = c_amt.number_input("金額 ($)", min_value=0.0, step=1.0, format="%.0f")
        
        period_input = st.selectbox("帳目性質", ["單次消費", "每月固定", "每週固定"])
        
        # 手機大按鈕
        submit_button = st.form_submit_button(label='🚀 點擊確認記帳')

if submit_button:
    if item_input.strip() == "":
        st.error("❌ 請輸入項目名稱！")
    elif amount_input <= 0:
        st.error("❌ 金額必須大於 0！")
    else:
        new_data = pd.DataFrame([[date_input.strftime("%Y-%m-%d"), type_input, item_input, category_input, amount_input, period_input]], 
                                columns=["日期", "類型", "項目", "類別", "金額", "週期性"])
        new_data.to_csv(FILE_NAME, mode='a', header=False, index=False, encoding='utf-8-sig')
        st.success(f"✅ 已記錄：{item_input} ${amount_input}")
        st.rerun()

# ================= 主畫面邏輯 =================
if os.path.exists(FILE_NAME):
    try:
        df = pd.read_csv(FILE_NAME, dtype={"日期": str}, encoding='utf-8-sig')
    except:
        df = pd.DataFrame(columns=["日期", "類型", "項目", "類別", "金額", "週期性"])
    
    df["週期性"] = df["週期性"].fillna("單次消費")
    
    if not df.empty:
        calc_df = df.copy()
        calc_df['日期'] = pd.to_datetime(calc_df['日期'])
        calc_df['月份'] = calc_df['日期'].dt.strftime('%Y-%m')
        calc_df['金額'] = calc_df['金額'].astype(float)
        
        # 篩選器（手機版上下排列好選取）
        selected_month = st.selectbox("📅 選擇篩選月份：", ["全部月份"] + sorted(calc_df['月份'].unique().tolist(), reverse=True))
        selected_category = st.selectbox("🏷️ 選擇獨立類別：", ["全部類別"] + sorted(calc_df['類別'].dropna().unique().tolist()))
        
        filtered_calc = calc_df.copy()
        if selected_month != "全部月份":
            filtered_calc = filtered_calc[filtered_calc['月份'] == selected_month]
        if selected_category != "全部類別":
            filtered_calc = filtered_calc[filtered_calc['類別'] == selected_category]
            
        total_income = filtered_calc[filtered_calc['類型'] == "收入"]['金額'].sum()
        total_expense = filtered_calc[filtered_calc['類型'] == "支出"]['金額'].sum()
        balance = total_income - total_expense
        
        # 看板改為更適合手機閱讀的格式
        st.write("---")
        kpi_col1, kpi_col2 = st.columns(2)
        kpi_col1.metric(label="🟢 總收入", value=f"${total_income:,.0f}")
        kpi_col2.metric(label="🔴 總支出", value=f"${total_expense:,.0f}")
        st.metric(label="🙌 淨存下結餘", value=f"${balance:,.0f}")
            
        # 每月預算
        with st.expander("🎯 智慧每月預算控管", expanded=False):
            budget_limit = st.number_input("預算上限 ($)", min_value=100.0, value=20000.0, step=500.0, format="%.0f")
            if total_expense > budget_limit:
                st.error(f"🚨 已超支 ${(total_expense - budget_limit):,.0f}！")
            else:
                st.success(f"💪 剩餘 ${budget_limit - total_expense:,.0f} 可用。")
            st.progress(min(1.0, float(total_expense / budget_limit)))
        
        # ================= 圖表分析區 =================
        st.write("---")
        st.subheader("📈 數據圖表分析")
        
        expense_df = filtered_calc[filtered_calc['類型'] == "支出"]
        tab1, tab2, tab3 = st.tabs(["🏷️ 圓餅", "📅 趨勢", "📊 收支"])
        
        with tab1:
            if not expense_df.empty:
                cate_chart = expense_df.groupby("類別")["金額"].sum().reset_index()
                fig_pie = px.pie(cate_chart, values="金額", names="類別", hole=0.3, color_discrete_sequence=px.colors.qualitative.Pastel)
                fig_pie.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=250) # 縮小圖表高度適合手機
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("沒有支出數據。")
                
        with tab2:
            if not expense_df.empty:
                df_trend = expense_df.groupby(expense_df['日期'].dt.strftime('%Y-%m-%d'))["金額"].sum().reset_index()
                fig_line = px.line(df_trend, x="日期", y="金額", markers=True, line_shape="spline")
                fig_line.update_layout(height=250)
                st.plotly_chart(fig_line, use_container_width=True)
            else:
                st.info("沒有支出數據。")
                
        with tab3:
            summary_data = pd.DataFrame({"財務類型": ["收入", "支出"], "金額 ($)": [total_income, total_expense]})
            fig_bar = px.bar(summary_data, x="財務類型", y="金額 ($)", color="財務類型", color_discrete_map={"收入": "#2ecc71", "支出": "#e74c3c"})
            fig_bar.update_layout(height=250)
            st.plotly_chart(fig_bar, use_container_width=True)
            
        # ================= 📋 全功能 Excel 編輯與刪除區 =================
        st.write("---")
        st.subheader("📋 帳目歷史明細")
        st.caption("💡 提示：橫向滑動表格可看完整欄位，按兩下格子直接修改。")
        
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
        
        # 適合手機滑動的資料編輯器
        edited_df = st.data_editor(
            df_filtered_edit,
            column_config={
                "原始索引": None,
                "日期": st.column_config.TextColumn("日期"),
                "類型": st.column_config.SelectboxColumn("類型", options=["支出", "收入"], required=True),
                "項目": st.column_config.TextColumn("項目"),
                "類別": st.column_config.SelectboxColumn("類別", options=["飲食", "交通", "娛樂", "購物", "居住房租", "水電通訊", "醫療保健", "薪水", "獎金", "投資收益", "零用錢", "副業收入", "其他"]),
                "金額": st.column_config.NumberColumn("金額", min_value=0.0, format="$ %.0f"),
                "週期性": st.column_config.SelectboxColumn("性質", options=["單次消費", "每月固定", "每週固定"])
            },
            use_container_width=True,
            num_rows="dynamic",
            height=300 # 限制高度，防止手機滑不到底部
        )
        
        if st.button("💾 儲存所有修改", type="primary", use_container_width=True):
            full_df = pd.read_csv(FILE_NAME, dtype={"日期": str}, encoding='utf-8-sig')
            for idx, row in edited_df.iterrows():
                orig_idx = row['原始索引']
                full_df.loc[orig_idx, ["日期", "類型", "項目", "類別", "金額", "週期性"]] = [row["日期"], row["類型"], row["項目"], row["類別"], row["金額"], row["週期性"]]
                
            current_visible_orig_indices = edited_df['原始索引'].tolist()
            for orig_idx in df_filtered_edit['原始索引'].tolist():
                if orig_idx not in current_visible_orig_indices:
                    full_df = full_df.drop(orig_idx)
                    
            full_df.to_csv(FILE_NAME, index=False, encoding='utf-8-sig')
            st.success("🎉 修改已儲存！")
            st.rerun()
            
    else:
        st.info("目前沒有紀錄，快新增第一筆吧！")
