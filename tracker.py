import streamlit as st
import pandas as pd
import os
from datetime import datetime

FILE_NAME = "expense_tracker.csv"

# 初始化資料檔案（新增'類型'欄位來區分 收入/支出）
if not os.path.exists(FILE_NAME):
    df = pd.DataFrame(columns=["日期", "類型", "項目", "類別", "金額"])
    df.to_csv(FILE_NAME, index=False, encoding='utf-8-sig')
else:
    # 舊資料相容處理：如果發現是舊版表格，自動升級格式
    df_check = pd.read_csv(FILE_NAME, encoding='utf-8-sig')
    if "類型" not in df_check.columns:
        st.warning("⚠️ 偵測到舊版資料格式，正在自動升級為『收入/支出』記帳本...")
        if "類別" in df_check.columns:
            df_check.insert(1, "類型", "支出")
        else:
            # 最早期的版本
            df_check.insert(1, "類型", "支出")
            df_check.insert(3, "類別", "未分類")
        df_check.to_csv(FILE_NAME, index=False, encoding='utf-8-sig')

# 網頁配置
st.set_page_config(page_title="天天記帳本", page_icon="💰", layout="centered")
st.title("💰 我的天天記帳本 App")

# 側邊欄：新增帳目
st.sidebar.header("✍️ 新增一筆紀錄")
with st.sidebar.form(key='expense_form', clear_on_submit=True):
    # 讓使用者選是收入還是支出
    type_input = st.sidebar.radio("帳目類型", ["支出", "收入"], horizontal=True)
    
    date_input = st.date_input("日期", datetime.now())
    item_input = st.text_input("項目名稱 (例如: 薪水 / 叉燒飯)", "")
    
    # 根據選收入或支出，提供不同的預設類別
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
        # 寫入 CSV
        new_data = pd.DataFrame([[date_input.strftime("%Y-%m-%d"), type_input, item_input, category_input, amount_input]], 
                                columns=["日期", "類型", "項目", "類別", "金額"])
        new_data.to_csv(FILE_NAME, mode='a', header=False, index=False, encoding='utf-8-sig')
        st.sidebar.success(f"✅ 成功記錄{type_input}：{item_input} ${amount_input}")

# 主畫面：讀取與顯示資料
if os.path.exists(FILE_NAME):
    try:
        df = pd.read_csv(FILE_NAME, encoding='utf-8-sig')
    except:
        df = pd.DataFrame(columns=["日期", "類型", "項目", "類別", "金額"])
    
    if not df.empty:
        st.subheader("📊 歷史帳目查看")
        
        # 處理日期與月份
        df['日期'] = pd.to_datetime(df['日期'])
        df['月份'] = df['日期'].dt.strftime('%Y-%m')
        
        month_list = ["全部"] + sorted(df['月份'].unique().tolist(), reverse=True)
        selected_month = st.selectbox("選擇篩選月份：", month_list)
        
        # 根據月份篩選
        if selected_month != "全部":
            filtered_df = df[df['月份'] == selected_month]
        else:
            filtered_df = df
            
        # 計算收入、支出、結餘
        total_income = filtered_df[filtered_df['類型'] == "收入"]['金額'].sum()
        total_expense = filtered_df[filtered_df['類型'] == "支出"]['金額'].sum()
        balance = total_income - total_expense
        
        # 顯示三大指標卡片
        col1, col2, col3 = st.columns(3)
        col1.metric(label="🟢 當月總收入", value=f"${total_income:,.2f}")
        col2.metric(label="🔴 當月總支出", value=f"${total_expense:,.2f}")
        
        # 結餘如果是正的顯示綠色（或正常顏色），負的提醒
        if balance >= 0:
            col3.metric(label="🙌 當
