import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from utils import load_all, sidebar_filters

# 0. 설정 및 데이터 로드
st.set_page_config(layout="wide")
power, daily, sector, supply = load_all()

# --- [추가] 계절 컬럼 생성 로직 ---
season_map = {
    12: "겨울", 1: "겨울", 2: "겨울",
    3: "봄", 4: "봄", 5: "봄",
    6: "여름", 7: "여름", 8: "여름",
    9: "가을", 10: "가을", 11: "가을",
}
# daily 데이터프레임에 계절 정보 추가
if "월" in daily.columns:
    daily["계절"] = daily["월"].map(season_map)
# ------------------------------

reg_sel, h_rng, d_rng = sidebar_filters(power, daily)

# 데이터 필터링
start, end = pd.to_datetime(d_rng[0]), pd.to_datetime(d_rng[1])
f_dy = daily[(daily["지역"] == reg_sel) & (daily["date"].between(start, end))].copy()
all_dy = daily[daily["date"].between(start, end)].copy()

st.title("기온 및 기상 요소 분석")
st.markdown("---")

# 1. 날짜별 혼합 차트 (전력량 + 기상 요소)
st.subheader("🌡️ 날짜별 전력 사용량과 기상 데이터 비교")
weather_opt = st.selectbox("비교 기상 요소 선택", ["temp", "강수량", "습도"], 
                     format_func=lambda x: {"temp":"기온","강수량":"강수량","습도":"습도"}[x])

weather_label = {"temp": "기온(℃)", "강수량": "강수량(mm)", "습도": "습도(%)"}[weather_opt]

fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.add_trace(go.Bar(x=f_dy["date"], y=f_dy["power_usage"], name="일별 전력 사용량", opacity=0.65), secondary_y=False)
fig.add_trace(go.Scatter(x=f_dy["date"], y=f_dy["rolling_mean_7"], name="7일 이동평균", mode="lines"), secondary_y=False)
fig.add_trace(go.Scatter(x=f_dy["date"], y=f_dy[weather_opt], name=weather_label, mode="lines+markers"), secondary_y=True)

fig.update_layout(hovermode="x unified", legend=dict(orientation="h", y=1.1), height=500)
fig.update_yaxes(title_text="전력 사용량(MWh)", secondary_y=False)
fig.update_yaxes(title_text=weather_label, secondary_y=True)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# 2. 기상 요소별 전력 사용량 관계 (통합 코드의 산점도 스타일 적용)
st.subheader(f"📊 {reg_sel} 기상 요소별 전력 사용량 관계")

if not f_dy.empty:
    sc_col1, sc_col2, sc_col3 = st.columns(3)

    with sc_col1:
        fig_temp = px.scatter(
            f_dy, x="temp", y="power_usage", color="계절", trendline="ols",
            title="기온 vs 전력 사용량",
            labels={"temp": "기온(℃)", "power_usage": "전력 사용량(MWh)", "계절": "계절"},
            color_discrete_map={"봄": "#2ecc71", "여름": "#e74c3c", "가을": "#f39c12", "겨울": "#3498db"}
        )
        st.plotly_chart(fig_temp, use_container_width=True)

    with sc_col2:
        fig_rain = px.scatter(
            f_dy, x="강수량", y="power_usage", color="계절", trendline="ols",
            title="강수량 vs 전력 사용량",
            labels={"강수량": "강수량(mm)", "power_usage": "전력 사용량(MWh)", "계절": "계절"},
            color_discrete_map={"봄": "#2ecc71", "여름": "#e74c3c", "가을": "#f39c12", "겨울": "#3498db"}
        )
        st.plotly_chart(fig_rain, use_container_width=True)

    with sc_col3:
        fig_humidity = px.scatter(
            f_dy, x="습도", y="power_usage", color="계절", trendline="ols",
            title="습도 vs 전력 사용량",
            labels={"습도": "습도(%)", "power_usage": "전력 사용량(MWh)", "계절": "계절"},
            color_discrete_map={"봄": "#2ecc71", "여름": "#e74c3c", "가을": "#f39c12", "겨울": "#3498db"}
        )
        st.plotly_chart(fig_humidity, use_container_width=True)
else:
    st.warning("선택한 범위에 데이터가 없습니다.")

st.divider()

# 3. 지역별 기온 민감도 랭킹
st.subheader("🌡️ 지역별 기온 민감도 랭킹")
corr_data = []
for r in all_dy["지역"].unique():
    tmp = all_dy[all_dy["지역"] == r]
    if len(tmp) > 5:
        temp_corr = tmp["power_usage"].corr(tmp["temp"])
        r_type = sector[sector["지역"] == r]["지역유형"].iloc[0] if r in sector["지역"].values else "N/A"
        corr_data.append({
            "지역": r, 
            "기온상관계수": temp_corr,
            "기온상관계수_절대값": abs(temp_corr),
            "지역유형": r_type
        })

if corr_data:
    corr_df = pd.DataFrame(corr_data).sort_values("기온상관계수_절대값", ascending=True)
    fig_corr = px.bar(
        corr_df, x="기온상관계수", y="지역", color="지역유형", orientation="h",
        title="지역별 기온-전력 상관계수 (절대값 순 정렬)",
        height=700
    )
    fig_corr.update_yaxes(categoryorder="array", categoryarray=corr_df["지역"].tolist())
    st.plotly_chart(fig_corr, use_container_width=True)
