import streamlit as st
import pandas as pd
import os
from datetime import datetime

FILE_NAME = "expense_tracker.csv"

# 初始化資料檔案
if not os.path.exists(FILE_NAME):
    df = pd.DataFrame(columns=["日期", "項目", "類別", "金額"])
    df.to_csv(FILE_NAME, index=False, encoding='utf-8-sig')

# 網頁標題
st.set_page_config(page_title="天天記帳本", page_icon="💰", layout="centered")
st.title("💰 我的天天記帳本 App")

# 側邊欄：新增消費
st.sidebar.header("✍️ 新增一筆消費")
with st.sidebar.form(key='expense_form', clear_on_submit=True):
    date_input = st.date_input("日期", datetime.now())
    item_input = st.text_input("消費項目 (例如: 叉燒飯)", "")
    category_input = st.selectbox("消費類別", ["飲食", "交通", "娛樂", "購物", "其他"])
    amount_input = st.number_input("金額 ($)", min_value=0.0, step=0.5)
    
    submit_button = st.form_submit_button(label='確認記帳')

if submit_button:
    if item_input.strip() == "":
        st.sidebar.error("❌ 請輸入消費項目！")
    elif amount_input <= 0:
        st.sidebar.error("❌ 金額必須大於 0！")
    else:
        # 寫入 CSV
        new_data = pd.DataFrame([[date_input.strftime("%Y-%m-%d"), item_input, category_input, amount_input]], 
                                columns=["日期", "項目", "類別", "金額"])
        new_data.to_csv(FILE_NAME, mode='a', header=False, index=False, encoding='utf-8-sig')
        st.sidebar.success(f"✅ 成功記錄：{item_input} ${amount_input}")

# 主畫面：讀取與顯示資料
if os.path.exists(FILE_NAME):
    try:
        df = pd.read_csv(FILE_NAME, encoding='utf-8-sig')
    except:
        df = pd.DataFrame(columns=["日期", "項目", "類別", "金額"])
    
    if not df.empty:
        # 月份篩選功能
        st.subheader("📊 歷史帳目查看")
        df['日期'] = pd.to_datetime(df['日期'])
        df['月份'] = df['日期'].dt.strftime('%Y-%m')
        
        month_list = ["全部"] + sorted(df['月份'].unique().tolist(), reverse=True)
        selected_month = st.selectbox("選擇篩選月份：", month_list)
        
        # 根據選擇篩選資料
        if selected_month != "全部":
            filtered_df = df[df['月份'] == selected_month]
        else:
            filtered_df = df
            
        # 重新將日期轉回字串美化顯示
        display_df = filtered_df.copy()
        display_df['日期'] = display_df['日期'].dt.strftime('%Y-%m-%d')
        
        # 顯示總金額卡片
        total_spent = filtered_df['金額'].sum()
        st.metric(label=f"限時總花費 ({selected_month})", value=f"${total_spent:,.2f}")
        
        # 顯示資料表格
        st.dataframe(display_df[["日期", "項目", "類別", "金額"]], use_container_width=True)
    else:
        st.info("目前還沒有任何消費紀錄，快從左邊新增第一筆吧！")