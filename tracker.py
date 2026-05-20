import streamlit as st
import pandas as pd
import os
import plotly.express as px
from datetime import datetime

FILE_NAME = "expense_tracker.csv"

# 初始化資料檔案
if not os.path.exists(FILE_NAME):
    df = pd.DataFrame(columns=["日期", "類型", "項目", "類別", "金額"])
    df.to_csv(FILE_NAME, index=False, encoding='utf-8-sig')
else:
    df_check = pd.read_csv(FILE_NAME, encoding='utf-8-sig')
    if "類型" not in df_check.columns:
        st.warning("⚠️ 正在更新資料格式...")
        df_check.insert(1, "類型", "支出")
        df_check.to_csv(FILE_NAME, index=False, encoding='utf-8-sig')

# 網頁配置
st.set_page_config(page_title="天天記帳本", page_icon="💰", layout="centered")
st.title("💰 我的天天記帳本 App")

# 側邊欄：新增帳目
st.sidebar.header("✍️ 新增一筆紀錄")
with st.sidebar.form(key='expense_form', clear_on_submit=True):
    type_input = st.sidebar.radio("帳目類型", ["支出", "收入"], horizontal=True)
    date_input = st.date_input("日期", datetime.now())
    item_input = st.text_input("項目名稱 (例如: 薪水 / 叉燒飯)", "")
    
    if type_input == "支出":
        categories = ["飲食", "交通", "娛樂", "購物", "其他"]
    else:
        categories = ["薪水", "獎金", "投資", "零用錢", "其他"]
        
    category_input = st.selectbox("項目類別", categories)
    amount_input = st.number_input("金額 ($)", min_value=0.0, step=0.5)
    
    submit_button = st.form_submit_button(label='確認記帳')

if submit_button:
    if item_input.strip() == "":
        st.sidebar.error("❌ 請輸入項目名稱！")
    elif amount_input <= 0:
        st.sidebar.error("❌ 金額必須大於 0！")
    else:
        new_data = pd.DataFrame([[date_input.strftime("%Y-%m-%d"), type_input, item_input, category_input, amount_input]], 
                                columns=["日期", "類型", "項目", "類別", "金額"])
        new_data.to_csv(FILE_NAME, mode='a', header=False, index=False, encoding='utf-8-sig')
        st.sidebar.success(f"✅ 成功記錄{type_input}：{item_input} ${amount_input}")
        st.rerun()

# 主畫面：讀取與顯示資料
if os.path.exists(FILE_NAME):
    try:
        df = pd.read_csv(FILE_NAME, dtype={"日期": str}, encoding='utf-8-sig')
    except:
        df = pd.DataFrame(columns=["日期", "類型", "項目", "類別", "金額"])
    
    if not df.empty:
        st.subheader("📊 歷史帳目查看與雙重篩選")
        
        # 數據轉換處理
        calc_df = df.copy()
        calc_df['日期'] = pd.to_datetime(calc_df['日期'])
        calc_df['月份'] = calc_df['日期'].dt.strftime('%Y-%m')
        calc_df['金額'] = calc_df['金額'].astype(float)
        
        # 建立雙排篩選器
        filter_col1, filter_col2 = st.columns(2)
        
        # 1. 月份篩選
        month_list = ["全部月份"] + sorted(calc_df['月份'].unique().tolist(), reverse=True)
        selected_month = filter_col1.selectbox("📅 選擇篩選月份：", month_list)
        
        # 2. 核心新增：獨立類別篩選
        all_categories = ["全部類別"] + sorted(calc_df['類別'].dropna().unique().tolist())
        selected_category = filter_col2.selectbox("🏷️ 選擇獨立項目類別：", all_categories)
        
        # 開始動態篩選資料
        filtered_calc = calc_df.copy()
        if selected_month != "全部月份":
            filtered_calc = filtered_calc[filtered_calc['月份'] == selected_month]
        if selected_category != "全部類別":
            filtered_calc = filtered_calc[filtered_calc['類別'] == selected_category]
            
        # 計算篩選後的數據
        total_income = filtered_calc[filtered_calc['類型'] == "收入"]['金額'].sum()
        total_expense = filtered_calc[filtered_calc['類型'] == "支出"]['金額'].sum()
        balance = total_income - total_expense
        
        # 數據看板
        col1, col2, col3 = st.columns(3)
        col1.metric(label="🟢 篩選總收入", value=f"${total_income:,.2f}")
        col2.metric(label="🔴 篩選總支出", value=f"${total_expense:,.2f}")
        if balance >= 0:
            col3.metric(label="🙌 篩選淨結餘", value=f"${balance:,.2f}")
        else:
            col3.metric(label="⚠️ 篩選淨結餘", value=f"${balance:,.2f}")
        
        # ------------------ 📈 圖表區塊 ------------------
        st.write("---")
        st.subheader("📈 支出數據圖表分析")
        
        expense_df = filtered_calc[filtered_calc['類型'] == "支出"]
        
        if not expense_df.empty:
            tab1, tab2 = st.tabs(["🏷️ 類別比例 (圓餅圖)", "📅 每日趨勢 (折線圖)"])
            
            with tab1:
                st.write("#### 各類別支出佔比")
                cate_chart = expense_df.groupby("類別")["金額"].sum().reset_index()
                fig_pie = px.pie(cate_chart, values="金額", names="類別", hole=0.3)
                fig_pie.update_layout(margin=dict(t=10, b=10, l=10, r=10))
                st.plotly_chart(fig_pie, use_container_width=True)
                
            with tab2:
                st.write("#### 每日花費走勢")
                df_trend = expense_df.groupby(expense_df['日期'].dt.strftime('%Y-%m-%d'))["金額"].sum().reset_index()
                fig_line = px.line(df_trend, x="日期", y="金額", markers=True)
                st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.info("當前篩選範圍內沒有支出紀錄（如果只選取收入類別，這裡也會是空的喔）。")
            
        # ------------------ 📋 全功能 Excel 編輯區塊 ------------------
        st.write("---")
        st.subheader("📋 帳目明細與編輯清單")
        st.caption("💡 提示：此表格會同步上方的篩選條件。你依然可以雙擊任何格子直接修改變數，改完點擊下方儲存。")
        
        # 為原始的 df 綁定索引，確保過濾後修改不會錯位
        df['原始索引'] = df.index
        
        # 依照選擇條件同步過濾底部的 Excel 表格
        df_filtered_edit = df.copy()
        df_filtered_edit['臨時日期'] = pd.to_datetime(df_filtered_edit['日期'])
        df_filtered_edit['臨時月份'] = df_filtered_edit['臨時日期'].dt.strftime('%Y-%m')
        
        if selected_month != "全部月份":
            df_filtered_edit = df_filtered_edit[df_filtered_edit['臨時月份'] == selected_month]
        if selected_category != "全部類別":
            df_filtered_edit = df_filtered_edit[df_filtered_edit['類別'] == selected_category]
            
        # 移除臨時欄位並倒序排列
        df_filtered_edit = df_filtered_edit.drop(columns=['臨時日期', '臨時月份'])
        df_filtered_edit = df_filtered_edit.iloc[::-1].reset_index(drop=True)
        
        # 顯示可編輯表格
        edited_df = st.data_editor(
            df_filtered_edit,
            column_config={
                "原始索引": None,  # 隱藏後台索引不給看
                "日期": st.column_config.TextColumn("日期 (YYYY-MM-DD)"),
                "類型": st.column_config.SelectboxColumn("類型", options=["支出", "收入"], required=True),
                "項目": st.column_config.TextColumn("項目名稱"),
                "類別": st.column_config.SelectboxColumn("類別", options=["飲食", "交通", "娛樂", "購物", "薪水", "獎金", "投資", "零用錢", "其他"]),
                "金額": st.column_config.NumberColumn("金額 ($)", min_value=0.0, format="$ %.2f"),
            },
            use_container_width=True,
            num_rows="dynamic"
        )
        
        # 儲存修改
        if st.button("💾 儲存所有修改", type="primary", use_container_width=True):
            full_df = pd.read_csv(FILE_NAME, dtype={"日期": str}, encoding='utf-8-sig')
            
            # 把使用者在畫面改好的資料，精準寫回完整資料庫中
            for idx, row in edited_df.iterrows():
                orig_idx = row['原始索引']
                full_df.loc[orig_idx, ["日期", "類型", "項目", "類別", "金額"]] = [row["日期"], row["類型"], row["項目"], row["類別"], row["金額"]]
                
            # 處理可能被刪除的行數
            current_visible_orig_indices = edited_df['原始索引'].tolist()
            # 如果原本存在於這個篩選條件中，但現在在編輯器裡不見了，代表被使用者刪除了
            for orig_idx in df_filtered_edit['原始索引'].tolist():
                if orig_idx not in current_visible_orig_indices:
                    full_df = full_df.drop(orig_idx)
                    
            full_df.to_csv(FILE_NAME, index=False, encoding='utf-8-sig')
            st.success("🎉 篩選後的修改已成功更新到雲端！")
            st.rerun()
            
    else:
        st.info("目前還沒有任何紀錄，快從左邊新增第一筆吧！")
