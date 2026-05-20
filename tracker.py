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
        df = pd.read_csv(FILE_NAME, encoding='utf-8-sig')
    except:
        df = pd.DataFrame(columns=["日期", "類型", "項目", "類別", "金額"])
    
    if not df.empty:
        st.subheader("📊 歷史帳目查看")
        
        df['日期'] = pd.to_datetime(df['日期'])
        df['月份'] = df['日期'].dt.strftime('%Y-%m')
        df['金額'] = df['金額'].astype(float)
        
        month_list = ["全部"] + sorted(df['月份'].unique().tolist(), reverse=True)
        selected_month = st.selectbox("選擇篩選月份：", month_list)
        
        if selected_month != "全部":
            filtered_df = df[df['月份'] == selected_month]
        else:
            filtered_df = df
            
        # 計算數據
        total_income = filtered_df[filtered_df['類型'] == "收入"]['金額'].sum()
        total_expense = filtered_df[filtered_df['類型'] == "支出"]['金額'].sum()
        balance = total_income - total_expense
        
        # 數據看板
        col1, col2, col3 = st.columns(3)
        col1.metric(label="🟢 當月總收入", value=f"${total_income:,.2f}")
        col2.metric(label="🔴 當月總支出", value=f"${total_expense:,.2f}")
        if balance >= 0:
            col3.metric(label="🙌 當月淨結餘 (存下)", value=f"${balance:,.2f}")
        else:
            col3.metric(label="⚠️ 當月淨結餘 (超支)", value=f"${balance:,.2f}")
        
        # ------------------ 📈 圖表區塊 ------------------
        st.write("---")
        st.subheader("📈 支出數據圖表分析")
        
        expense_df = filtered_df[filtered_df['類型'] == "支出"]
        
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
                # 這裡把欄位對齊，修正為正確的「日期」欄位
                df_trend = expense_df.groupby(expense_df['日期'].dt.strftime('%Y-%m-%d'))["金額"].sum().reset_index()
                fig_line = px.line(df_trend, x="日期", y="金額", markers=True)
                st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.info("當前篩選範圍內沒有任何支出紀錄，無法產生圖表。")
            
        st.write("---")
        st.subheader("📋 帳目明細與刪除")
        
        # 給原始的 df 建立一個暫時的索引 ID（用來精準刪除某一行）
        df['原始索引'] = df.index
        
        # 再次過濾要顯示的部分
        if selected_month != "全部":
            display_df = df[df['月份'] == selected_month].copy()
        else:
            display_df = df.copy()
            
        display_df['日期'] = display_df['日期'].dt.strftime('%Y-%m-%d')
        display_df = display_df.sort_values(by="日期", ascending=False)
        
        # 用循環一行一行印出資料，並在後面加一個刪除按鈕
        for idx, row in display_df.iterrows():
            with st.container():
                c1, c2, c3, c4, c5 = st.columns([2, 1, 3, 2, 1])
                c1.write(f"📅 {row['日期']}")
                if row['類型'] == "收入":
                    c2.markdown("🟢")
                else:
                    c2.markdown("🔴")
                c3.write(f"**{row['項目']}** ({row['類別']})")
                c4.write(f"${float(row['金額']):,.1f}")
                
                # 刪除功能
                if c5.button("🗑️", key=f"del_{row['原始索引']}"):
                    full_df = pd.read_csv(FILE_NAME, encoding='utf-8-sig')
                    full_df = full_df.drop(row['原始索引'])
                    full_df.to_csv(FILE_NAME, index=False, encoding='utf-8-sig')
                    st.success("刪除成功！正在重整...")
                    st.rerun()
    else:
        st.info("目前還沒有任何紀錄，快從左邊新增第一筆吧！")
