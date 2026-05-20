import streamlit as st
import pandas as pd
import os
import plotly.express as px
from datetime import datetime
import requests
from streamlit_lottie import st_lottie

FILE_NAME = "expense_tracker.csv"

# 載入 Lottie 動畫的輔助函式
def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

# 取得免費且精美的記帳動畫 JSON (金幣與錢包)
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

# 網頁配置
st.set_page_config(page_title="極致動感記帳本", page_icon="🏆", layout="centered")

# 注入 CSS 動畫樣式 (淡入效果)
st.markdown("""
    <style>
    /* 讓主畫面元件擁有流暢的淡入流暢動畫 */
    .stApp {
        animation: fadeIn 1.2s ease-in-out;
    }
    @keyframes fadeIn {
        0% { opacity: 0; transform: translateY(10px); }
        100% { opacity: 1; transform: translateY(0); }
    }
    /* 美化進度條 */
    .stProgress > div > div > div > div {
        background-image: linear-gradient(to right, #4facfe 0%, #00f2fe 100%);
    }
    </style>
""", unsafe_allow_html=True)

# 頂部迎賓區：標題與流暢動態圖卡並排
col_title, col_anim = st.columns([2, 1])
with col_title:
    st.title("🏆 我的智慧動感記帳本")
    st.caption("🚀 融合全網精華與動態美學：網頁元件已全面啟用 Smooth 淡入動畫效果")
with col_anim:
    if lottie_wallet:
        st_lottie(lottie_wallet, speed=1, reverse=False, loop=True, height=100, key="wallet")

# ================= 側邊欄：新增帳目 =================
st.sidebar.header("✍️ 新增一筆紀錄")
with st.sidebar.form(key='expense_form', clear_on_submit=True):
    type_input = st.sidebar.radio("帳目類型", ["支出", "收入"], horizontal=True)
    date_input = st.date_input("日期", datetime.now())
    item_input = st.text_input("項目名稱 (例如: 麥當勞 / 月結薪水)", "")
    
    if type_input == "支出":
        categories = ["飲食", "交通", "娛樂", "購物", "居住房租", "水電通訊", "醫療保健", "其他"]
    else:
        categories = ["薪水", "獎金", "投資收益", "零用錢", "副業收入", "其他"]
        
    category_input = st.selectbox("項目類別", categories)
    amount_input = st.number_input("金額 ($)", min_value=0.0, step=1.0)
    period_input = st.selectbox("這筆帳目的重複週期", ["單次消費", "每月固定(如房租/薪水)", "每週固定"])
    
    submit_button = st.form_submit_button(label='確認記帳')

if submit_button:
    if item_input.strip() == "":
        st.sidebar.error("❌ 請輸入項目名稱！")
    elif amount_input <= 0:
        st.sidebar.error("❌ 金額必須大於 0！")
    else:
        new_data = pd.DataFrame([[date_input.strftime("%Y-%m-%d"), type_input, item_input, category_input, amount_input, period_input]], 
                                columns=["日期", "類型", "項目", "類別", "金額", "週期性"])
        new_data.to_csv(FILE_NAME, mode='a', header=False, index=False, encoding='utf-8-sig')
        st.sidebar.success(f"✅ 成功記錄：{item_input} ${amount_input}")
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
        
        filter_col1, filter_col2 = st.columns(2)
        month_list = ["全部月份"] + sorted(calc_df['月份'].unique().tolist(), reverse=True)
        selected_month = filter_col1.selectbox("📅 選擇篩選月份：", month_list)
        
        all_categories = ["全部類別"] + sorted(calc_df['類別'].dropna().unique().tolist())
        selected_category = filter_col2.selectbox("🏷️ 選擇獨立項目類別：", all_categories)
        
        filtered_calc = calc_df.copy()
        if selected_month != "全部月份":
            filtered_calc = filtered_calc[filtered_calc['月份'] == selected_month]
        if selected_category != "全部類別":
            filtered_calc = filtered_calc[filtered_calc['類別'] == selected_category]
            
        total_income = filtered_calc[filtered_calc['類型'] == "收入"]['金額'].sum()
        total_expense = filtered_calc[filtered_calc['類型'] == "支出"]['金額'].sum()
        balance = total_income - total_expense
        
        col1, col2, col3 = st.columns(3)
        col1.metric(label="🟢 總收入", value=f"${total_income:,.2f}")
        col2.metric(label="🔴 總支出", value=f"${total_expense:,.2f}")
        if balance >= 0:
            col3.metric(label="🙌 淨存下結餘", value=f"${balance:,.2f}")
        else:
            col3.metric(label="⚠️ 當前呈透支", value=f"${balance:,.2f}")
            
        st.write("")
        with st.expander("🎯 智慧每月預算控管中心", expanded=False):
            budget_limit = st.number_input("設定你每個月的「最高支出預算上限」($)", min_value=100.0, value=20000.0, step=500.0)
            if total_expense > budget_limit:
                st.error(f"🚨 警告：你這個月已經超支了！超額了 ${(total_expense - budget_limit):,.1f}！")
            elif total_expense >= budget_limit * 0.8:
                st.warning(f"⚠️ 警報：本月花費已達預算的 {total_expense/budget_limit*100:.1f}%！")
            else:
                st.success(f"💪 目前花費僅佔預算的 {total_expense/budget_limit*100:.1f}%，還有 ${budget_limit - total_expense:,.1f} 可以使用。")
            progress_percent = min(1.0, float(total_expense / budget_limit))
            st.progress(progress_percent)
        
        # ================= 📈 圖表分析區 =================
        st.write("---")
        st.subheader("📈 智慧數據多元圖表分析")
        
        expense_df = filtered_calc[filtered_calc['類型'] == "支出"]
        tab1, tab2, tab3 = st.tabs(["🏷️ 類別比例 (圓餅圖)", "📅 每日趨勢 (折線圖)", "📊 收支對比 (長條圖)"])
        
        with tab1:
            if not expense_df.empty:
                st.write("#### 支出品項比例分佈")
                cate_chart = expense_df.groupby("類別")["金額"].sum().reset_index()
                fig_pie = px.pie(cate_chart, values="金額", names="類別", hole=0.3, color_discrete_sequence=px.colors.qualitative.Pastel)
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("當前篩選範圍內沒有支出數據。")
                
        with tab2:
            if not expense_df.empty:
                st.write("#### 本月每日花費走勢曲線")
                df_trend = expense_df.groupby(expense_df['日期'].dt.strftime('%Y-%m-%d'))["金額"].sum().reset_index()
                # 這裡加上了動畫線條平滑化 (spline) 效果
                fig_line = px.line(df_trend, x="日期", y="金額", markers=True, line_shape="spline")
                st.plotly_chart(fig_line, use_container_width=True)
            else:
                st.info("當前篩選範圍內沒有支出數據。")
                
        with tab3:
            st.write("#### 總收入與總支出直觀對比")
            summary_data = pd.DataFrame({
                "財務類型": ["總收入", "總支出"],
                "金額 ($)": [total_income, total_expense]
            })
            fig_bar = px.bar(summary_data, x="財務類型", y="金額 ($)", color="財務類型", color_discrete_map={"總收入": "#2ecc71", "總支出": "#e74c3c"})
            st.plotly_chart(fig_bar, use_container_width=True)
            
        # ================= 📋 全功能 Excel 編輯與刪除區 =================
        st.write("---")
        st.subheader("📋 帳目歷史明細")
        
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
        
        edited_df = st.data_editor(
            df_filtered_edit,
            column_config={
                "原始索引": None,
                "日期": st.column_config.TextColumn("消費日期 (YYYY-MM-DD)"),
                "類型": st.column_config.SelectboxColumn("帳目類型", options=["支出", "收入"], required=True),
                "項目": st.column_config.TextColumn("項目名稱"),
                "類別": st.column_config.SelectboxColumn("項目類別", options=["飲食", "交通", "娛樂", "購物", "居住房租", "水電通訊", "醫療保健", "薪水", "獎金", "投資收益", "零用錢", "副業收入", "其他"]),
                "金額": st.column_config.NumberColumn("金額 ($)", min_value=0.0, format="$ %.1f"),
                "週期性": st.column_config.SelectboxColumn("帳目性質", options=["單次消費", "每月固定(如房租/薪水)", "每週固定"])
            },
            use_container_width=True,
            num_rows="dynamic"
        )
        
        if st.button("💾 儲存所有變數修改", type="primary", use_container_width=True):
            full_df = pd.read_csv(FILE_NAME, dtype={"日期": str}, encoding='utf-8-sig')
            for idx, row in edited_df.iterrows():
                orig_idx = row['原始索引']
                full_df.loc[orig_idx, ["日期", "類型", "項目", "類別", "金額", "週期性"]] = [row["日期"], row["類型"], row["項目"], row["類別"], row["金額"], row["週期性"]]
                
            current_visible_orig_indices = edited_df['原始索引'].tolist()
            for orig_idx in df_filtered_edit['原始索引'].tolist():
                if orig_idx not in current_visible_orig_indices:
                    full_df = full_df.drop(orig_idx)
                    
            full_df.to_csv(FILE_NAME, index=False, encoding='utf-8-sig')
            st.success("🎉 修改與刪除均已成功更新！")
            st.rerun()
            
    else:
        st.info("目前還沒有任何紀錄，快從左邊新增第一筆吧！")
