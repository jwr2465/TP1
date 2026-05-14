import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np
from utils import load_all, sidebar_filters

st.set_page_config(layout="wide")
power, daily, sector, supply = load_all()
reg_sel, h_rng, d_rng = sidebar_filters(power, daily)

start, end = pd.to_datetime(d_rng[0]), pd.to_datetime(d_rng[1])
f_hr = power[(power["지역"]==reg_sel) & (power["시간"].between(*h_rng)) & (power["거래일자"].between(start, end))]
f_dy = daily[(daily["지역"]==reg_sel) & (daily["date"].between(start, end))]
all_hr = power[(power["시간"].between(*h_rng)) & (power["거래일자"].between(start, end))]

reg_tot = all_hr.groupby("지역")["전력거래량(MWh)"].sum().reset_index().sort_values("전력거래량(MWh)", ascending=False)
reg_tot = reg_tot.merge(sector[["지역", "산업비중(%)", "주거비중(%)", "지역유형"]], on="지역", how="left")

st.title("2024 지역별 전력 사용량 분석")
st.subheader(f"📊 {reg_sel} 전력 사용량 및 기상 요약")

col1, col2, col3, col4 = st.columns(4)
col1.metric("총 전력거래량", f"{f_hr['전력거래량(MWh)'].sum():,.0f} MWh")
col2.metric("평균 전력거래량", f"{f_hr['전력거래량(MWh)'].mean():,.2f} MWh")
col3.metric("최대 전력거래량", f"{f_hr['전력거래량(MWh)'].max():,.2f} MWh")
col4.metric("최소 전력거래량", f"{f_hr['전력거래량(MWh)'].min():,.2f} MWh")

col5, col6, col7, col8 = st.columns(4)
col5.metric("평균 기온", f"{f_dy['temp'].mean():.1f} ℃")
col6.metric("총 강수량", f"{f_dy['강수량'].sum():.1f} mm")
col7.metric("평균 습도", f"{f_dy['습도'].mean():.1f} %")
s_info = sector[sector["지역"] == reg_sel]
col8.metric("지역 유형", s_info["지역유형"].iloc[0] if not s_info.empty else "N/A", f"산업비중 {s_info['산업비중(%)'].iloc[0]:.1f}%" if not s_info.empty else None)

st.divider()
st.subheader("📍 지역별 전력 사용량 분포")
coords = {"서울특별시": [37.56, 126.97], "부산광역시": [35.17, 129.07], "대구광역시": [35.87, 128.60], "인천광역시": [37.45, 126.70], "광주광역시": [35.15, 126.85], "대전광역시": [36.35, 127.38], "울산광역시": [35.53, 129.31], "세종특별자치시": [36.48, 127.28], "경기도": [37.41, 127.51], "강원도": [37.82, 128.15], "충청북도": [36.80, 127.70], "충청남도": [36.51, 126.80], "전라북도": [35.71, 127.15], "전라남도": [34.86, 126.99], "경상북도": [36.49, 128.88], "경상남도": [35.46, 128.21], "제주특별자치도": [33.49, 126.53]}
map_df = reg_tot.copy()
map_df["lat"] = map_df["지역"].map(lambda x: coords.get(x, [np.nan]*2)[0])
map_df["lon"] = map_df["지역"].map(lambda x: coords.get(x, [np.nan]*2)[1])
fig_map = px.scatter_mapbox(map_df.dropna(), lat="lat", lon="lon", size="전력거래량(MWh)", color="전력거래량(MWh)", hover_name="지역", size_max=60, zoom=6.2, mapbox_style="carto-positron")
fig_map.update_layout(height=800, margin={"r":0,"t":0,"l":0,"b":0})
st.plotly_chart(fig_map, use_container_width=True)

c1, c2 = st.columns(2)
c1.plotly_chart(px.line(f_hr.groupby("시간")["전력거래량(MWh)"].mean().reset_index(), x="시간", y="전력거래량(MWh)", markers=True, title="시간대별 평균 패턴").update_layout(height=500), use_container_width=True)
c2.plotly_chart(px.bar(f_hr.groupby("월")["전력거래량(MWh)"].sum().reset_index(), x="월", y="전력거래량(MWh)", title="월별 총 사용량").update_layout(height=500), use_container_width=True)

c3, c4 = st.columns(2)
wd_order = ["월", "화", "수", "목", "금", "토", "일"]
f_wd = f_hr.groupby("요일", as_index=False)["전력거래량(MWh)"].mean()
f_wd["요일"] = pd.Categorical(f_wd["요일"], categories=wd_order, ordered=True)
c3.plotly_chart(px.bar(f_wd.sort_values("요일"), x="요일", y="전력거래량(MWh)", title="요일별 평균 전력량").update_layout(height=500), use_container_width=True)
c4.plotly_chart(px.line(f_hr.groupby("거래일자", as_index=False)["전력거래량(MWh)"].sum(), x="거래일자", y="전력거래량(MWh)", title="일자별 전력량 추이").update_layout(height=500), use_container_width=True)

st.divider()
peak_row = f_hr.loc[f_hr["전력거래량(MWh)"].idxmax()]
st.subheader("피크 전력 사용 시간")
p1, p2, p3, p4 = st.columns(4)
p1.metric("피크 날짜", peak_row["거래일자"].strftime("%Y-%m-%d"))
p2.metric("피크 시간", f"{int(peak_row['시간'])}시")
p3.metric("피크 전력량", f"{peak_row['전력거래량(MWh)']:,.2f} MWh")
p4.metric("피크 요일", peak_row["요일"])