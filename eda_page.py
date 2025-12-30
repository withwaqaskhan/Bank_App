import streamlit as st
import data_manager as dm
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def show():
    user = st.session_state.get('logged_in_user')
    if not user:
        st.session_state.page = "Login"
        st.rerun()
        return

    st.header("📊 Financial & Sentiment Analytics")
    
    # Tabs for organization
    tab1, tab2 = st.tabs(["💰 Financial EDA", "🤖 Sentiment Monitoring"])

    with tab1:
        # --- FINANCIAL EDA SECTION ---
        all_trans = dm.get_transactions()
        user_trans = [t for t in all_trans if t['sender'] == user['account_no'] or t['receiver_acc'] == user['account_no']]

        if not user_trans:
            st.info("Insufficient data for financial analysis.")
        else:
            df = pd.DataFrame(user_trans)
            df['date'] = pd.to_datetime(df['date'])
            df['amount'] = df['amount'].astype(float)
            df['day_name'] = df['date'].dt.day_name()

            # Top Metrics
            total_deposited = df[df['type'] == "Deposit"]['amount'].sum()
            total_transferred = df[(df['type'] == "Transfer") & (df['sender'] == user['account_no'])]['amount'].sum()
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Total Deposits", f"Rs. {total_deposited:,.0f}")
            m2.metric("Total Transfers", f"Rs. {total_transferred:,.0f}")
            m3.metric("Net Flow", f"Rs. {(total_deposited - total_transferred):,.0f}")

            st.divider()

            # --- GRAPH 1: TRANSACTION TRENDS (Existing) ---
            st.subheader("📈 Transaction Trends Over Time")
            trend_data = df.groupby(df['date'].dt.date)['amount'].sum().reset_index()
            st.line_chart(data=trend_data, x='date', y='amount')

            # --- NAYE GRAPHS KIYA ADD KIYE HAIN ---
            col_g1, col_g2 = st.columns(2)

            with col_g1:
                # --- GRAPH 2: TRANSACTION TYPE DISTRIBUTION (Donut Chart) ---
                st.subheader("🍕 Spending vs Savings")
                type_counts = df['type'].value_counts()
                fig2, ax2 = plt.subplots()
                ax2.pie(type_counts, labels=type_counts.index, autopct='%1.1f%%', 
                        startangle=90, colors=sns.color_palette("Set2"), wedgeprops=dict(width=0.4))
                st.pyplot(fig2)

            with col_g2:
                # --- GRAPH 3: AMOUNT DISTRIBUTION (Histogram) ---
                st.subheader("💰 Transaction Size Density")
                fig3, ax3 = plt.subplots()
                sns.histplot(df['amount'], kde=True, color="#ff6e40", ax=ax3)
                plt.xlabel("Amount (Rs.)")
                st.pyplot(fig3)

            st.divider()
            
            col_g3, col_g4 = st.columns(2)

            with col_g3:
                # --- GRAPH 4: DAILY CASH FLOW (Inflow vs Outflow Bar Chart) ---
                st.subheader("📅 Daily Cash Flow Analysis")
                # Simplified grouping for bar chart
                df['Flow'] = df.apply(lambda x: 'Inflow' if x['type'] == 'Deposit' else 'Outflow', axis=1)
                flow_data = df.groupby(['day_name', 'Flow'])['amount'].sum().unstack().fillna(0)
                
                fig4, ax4 = plt.subplots()
                flow_data.plot(kind='bar', ax=ax4, color=['#2ecc71', '#e74c3c'])
                plt.xticks(rotation=45)
                st.pyplot(fig4)

            with col_g4:
                # --- GRAPH 5: CUMULATIVE WEALTH GROWTH (Area Chart) ---
                st.subheader("🚀 Wealth Growth Timeline")
                df_sorted = df.sort_values('date')
                # Net impact calculation per transaction
                df_sorted['impact'] = df_sorted.apply(lambda x: x['amount'] if x['type'] == 'Deposit' else -x['amount'], axis=1)
                df_sorted['balance_history'] = df_sorted['impact'].cumsum()
                
                fig5, ax5 = plt.subplots()
                plt.fill_between(df_sorted['date'], df_sorted['balance_history'], color="skyblue", alpha=0.4)
                plt.plot(df_sorted['date'], df_sorted['balance_history'], color="Slateblue", alpha=0.6)
                plt.xticks(rotation=45)
                st.pyplot(fig5)

    with tab2:
        # --- SENTIMENT MONITORING SYSTEM (NO CHANGES AS PER REQUEST) ---
        st.subheader("🕵️ Customer Sentiment Inference")
        sentiment_data = dm.get_sentiment_logs()
        
        if not sentiment_data:
            st.info("No chatbot interactions recorded yet for sentiment analysis.")
        else:
            sent_df = pd.DataFrame(sentiment_data)
            sent_df['timestamp'] = pd.to_datetime(sent_df['timestamp'])
            
            st.write("### 📋 User Inference Table")
            display_df = sent_df[['user_name', 'account_no', 'message', 'sentiment']].tail(10)
            st.table(display_df)

            st.divider()

            st.write("### 🔥 Heatmap of Peak Frustration")
            neg_df = sent_df[sent_df['sentiment'] == "Negative"].copy()

            if neg_df.empty:
                st.success("No 'Negative' sentiments detected yet. Everything looks good!")
            else:
                neg_df['hour'] = neg_df['timestamp'].dt.hour
                neg_df['day'] = neg_df['timestamp'].dt.day_name()
                heatmap_data = neg_df.groupby(['day', 'hour']).size().unstack(fill_value=0)
                days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                heatmap_data = heatmap_data.reindex(days_order)

                fig, ax = plt.subplots(figsize=(10, 5))
                sns.heatmap(heatmap_data, annot=True, cmap="YlOrRd", fmt='g', ax=ax)
                st.pyplot(fig)

            st.divider()

            st.write("### 🧠 Advanced Sentiment Insights")
            selected_acc = st.selectbox("Select User Account for Deep Analysis", sent_df['account_no'].unique())
            user_logs = sent_df[sent_df['account_no'] == selected_acc]

            with st.expander("🔍 Click to Expand Deep Analysis", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Sentiment Distribution**")
                    sentiment_counts = user_logs['sentiment'].value_counts()
                    st.bar_chart(sentiment_counts)
                
                with col2:
                    last_log = user_logs.iloc[-1]
                    st.write("**Latest Incident Report**")
                    st.error(f"Problematic Word: `{last_log['important_word']}`")
                    st.info(f"Confidence Score: {last_log['confidence']}")
                    
                    if "Escalation" in last_log['action']:
                        st.warning(f"⚠️ Action: {last_log['action']}")
                    else:
                        st.success(f"✅ Action: {last_log['action']}")

                st.write("**Sentiment Drift (Timeline)**")
                st.line_chart(data=user_logs, x='timestamp', y='sentiment')

    st.divider()
    if st.button("⬅️ Back to Dashboard"):
        st.session_state.page = "Dashboard"
        st.rerun()