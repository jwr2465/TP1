import streamlit as st
import plotly.express as px
import pandas as pd
from utils import load_all, sidebar_filters

# 0. 설정 및 데이터 로드
st.set_page_config(layout="wide")
power, daily, sector, supply = load_all()
reg_sel, h_rng, d_rng = sidebar_filters(power, daily)

# 데이터 처리
start, end = pd.to_datetime(d_rng[0]), pd.to_datetime(d_rng[1])
f_sup = supply[supply["date"].between(start, end)].copy()
f_sup["월"] = f_sup["date"].dt.month
f_sup["일"] = f_sup["date"].dt.day

st.title("🚨 전력 수급 위기 진단 및 피크 집중 분석")
st.markdown("전력 위기는 무작위로 오지 않습니다. **특정 계절의 특정 시간**을 공략하는 맞춤형 관리가 필요합니다.")

# --- 1. 공급예비율 위험일 캘린더 히트맵 (진한 빨간색 강조) ---
st.subheader("🗓️ [시간] 공급예비율 위험일 캘린더 히트맵")
st.caption("공급예비율이 낮을수록(진한 빨간색) 수급 위험이 높음을 의미합니다.")

if not f_sup.empty:
    heatmap_data = f_sup.pivot_table(index="일", columns="월", values="공급예비율(%)", aggfunc='mean')
    
    # Reds_r: 낮은 값(위험)이 진한 빨강으로 표시됨
    fig_heatmap = px.imshow(
        heatmap_data,
        labels=dict(x="월", y="일", color="예비율(%)"),
        x=[f"{m}월" for m in heatmap_data.columns],
        y=heatmap_data.index,
        color_continuous_scale="Reds_r", 
        aspect="auto"
    )
    # y축을 역순으로 배치하여 1일이 위로 오게 함
    fig_heatmap.update_yaxes(autorange="reversed")
    st.plotly_chart(fig_heatmap, use_container_width=True)
    st.info("💡 **데이터 인사이트:** 8-9월 폭염 시기에 진한 빨간색(저예비율)이 집중됩니다. 사전 관리가 필수적인 구간입니다.")
else:
    st.warning("선택한 날짜 범위에 수급 데이터가 없습니다.")

st.divider()

# --- 2. 위험일 피크 시간 분포 ---
col_a, col_b = st.columns([3, 2])

with col_a:
    st.subheader("⏰ [시간] 수급 취약일의 피크 시간대")
    threshold = st.slider("위험 기준 예비율 설정(%)", 5, 20, 15)
    risk_days = f_sup[f_sup["공급예비율(%)"] < threshold].copy()
    
    if not risk_days.empty:
        # 시간 추출 로직 (최대전력기준일시 형식: 2024/08/13(17:00))
        risk_days["피크시간"] = risk_days["최대전력기준일시"].str.extract(r'\((\d{2}):').astype(int)
        
        fig_hist = px.bar(
            risk_days.groupby("피크시간").size().reset_index(name="count"),
            x="피크시간", y="count",
            title=f"예비율 {threshold}% 미만 위험일의 피크 시간 분포",
            labels={'피크시간': '시간 (시)', 'count': '발생 횟수(일)'},
            color_discrete_sequence=['#CC0000'] # 진한 빨강
        )
        fig_hist.update_layout(xaxis=dict(dtick=1))
        st.plotly_chart(fig_hist, use_container_width=True)
    else:
        st.write("선택한 기준 미만의 위험일이 없습니다.")

with col_b:
    st.subheader("🎯 피크 관리 필요성")
    if not risk_days.empty:
        peak_hour = risk_days['피크시간'].mode()[0]
        st.markdown(f"""
        전력 수급 위험은 특정 시간에 집중됩니다.
        - **분석 결과:** {peak_hour}시 전후 집중 발생
        - **결론:** 하루 전체 전력 절감보다 **피크 시간대 집중 관리**가 예비율 회복에 훨씬 효과적입니다.
        """)