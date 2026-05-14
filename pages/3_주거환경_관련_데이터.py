import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np
from utils import load_all, sidebar_filters, read_csv

# 0. 설정 및 데이터 로드
st.set_page_config(layout="wide")
power, daily, sector, supply = load_all()
reg_sel, h_rng, d_rng = sidebar_filters(power, daily)

# 데이터 필터링
start, end = pd.to_datetime(d_rng[0]), pd.to_datetime(d_rng[1])
all_hr = power[(power["시간"].between(*h_rng)) & (power["거래일자"].between(start, end))]
all_dy = daily[daily["date"].between(start, end)]

# 지역별 총량 및 특성 데이터 통합
reg_tot = all_hr.groupby("지역")["전력거래량(MWh)"].sum().reset_index().sort_values("전력거래량(MWh)", ascending=False)
reg_tot = reg_tot.merge(sector[["지역", "지역유형", "산업비중(%)", "주거비중(%)"]], on="지역", how="left")

# --- 분석 데이터 준비 함수 ---
@st.cache_data
def get_pop_energy_data():
    gen_df = read_csv("HOME_발전·판매_발전량_지역별.csv")
    pop_df = read_csv("202412_202412_연령별인구현황_연간.csv")
    
    if gen_df is None or pop_df is None: return pd.DataFrame()

    def norm_reg(name):
        if not isinstance(name, str): return name
        name = name.strip()
        mapping = {
            "서울": "서울특별시", "부산": "부산광역시", "대구": "대구광역시", "인천": "인천광역시",
            "광주": "광주광역시", "대전": "대전광역시", "울산": "울산광역시", "세종": "세종특별자치시",
            "경기": "경기도", "강원": "강원도", "충북": "충청북도", "충남": "충청남도",
            "전북": "전라북도", "전남": "전라남도", "경북": "경상북도", "경남": "경상남도", "제주": "제주특별자치도",
        }
        for short, full in mapping.items():
            if short in name: return full
        return name

    # 발전량 및 소비량 정리
    id_vars = ["연도"] if "연도" in gen_df.columns else [gen_df.columns[0]]
    cols = [c for c in gen_df.columns if c not in id_vars]
    gen_melt = gen_df.melt(id_vars=id_vars, value_vars=cols, var_name='지역', value_name='발전량(MWh)')
    gen_melt["지역"] = gen_melt["지역"].apply(norm_reg)
    
    cons_total = power.groupby("지역")["전력거래량(MWh)"].sum().reset_index()
    cons_total["지역"] = cons_total["지역"].apply(norm_reg)
    
    # 인구 데이터 정리
    pop_df['지역'] = pop_df['행정구역'].str.split('(').str[0].str.strip().apply(norm_reg)
    pop_col = [c for c in pop_df.columns if '총인구수' in c and '계' in c][0]
    pop_df['총인구수'] = pd.to_numeric(pop_df[pop_col].astype(str).str.replace(',', ''), errors='coerce')

    # 데이터 통합 및 지표 계산
    df = pd.merge(gen_melt, cons_total, on="지역", how="inner")
    df = pd.merge(df, pop_df[['지역', '총인구수']], on="지역", how="inner")

    df["자립도(%)"] = (df["발전량(MWh)"] / df["전력거래량(MWh)"]) * 100
    df["1인당_전력소비량(MWh)"] = df["전력거래량(MWh)"] / df["총인구수"]
    df["1인당_발전량(MWh)"] = df["발전량(MWh)"] / df["총인구수"]
    
    return df.dropna()

# --- UI 시작 ---
st.title("🏙️ 주거 환경 및 도시 유형 분석")

# 1. 상단 요약 지표 (유지)
st.subheader("📌 분석 기간 주요 지표")
m1, m2, m3, m4 = st.columns(4)
total_usage = reg_tot["전력거래량(MWh)"].sum()
avg_industry = reg_tot["산업비중(%)"].mean()
high_industry_city = reg_tot.loc[reg_tot["산업비중(%)"].idxmax(), "지역"] if not reg_tot["산업비중(%)"].isnull().all() else "N/A"
high_usage_city = reg_tot.iloc[0]["지역"] if not reg_tot.empty else "N/A"

m1.metric("총 전력 거래량", f"{total_usage/1000:,.1f} GWh")
m2.metric("평균 산업 비중", f"{avg_industry:.1f}%")
m3.metric("최대 사용 지역", high_usage_city)
m4.metric("산업 비중 1위", high_industry_city)

st.divider()

# 2. 지역별 용도별 비중 분석 (이 부분만 파란색 테마 누적 막대 그래프로 변경)
st.subheader("🏭 지역별 전력 소비 용도별 비중 (%)")

# 시각화를 위한 데이터 변환
reg_share = reg_tot.melt(
    id_vars=["지역", "지역유형"], 
    value_vars=["산업비중(%)", "주거비중(%)"],
    var_name="용도", 
    value_name="비중(%)"
)

fig_share = px.bar(
    reg_share, 
    x="지역", 
    y="비중(%)", 
    color="용도",
    title="지역별 전력 소비 비중 (산업 vs 주거)",
    labels={"비중(%)": "비중 (%)", "용도": "구분"},
    # 파란색 계열 테마 적용
    color_discrete_map={
        "산업비중(%)": "#1A365D", # Deep Navy
        "주거비중(%)": "#63B3ED"  # Sky Blue
    },
    barmode="stack"
)

fig_share.update_layout(
    height=500, 
    yaxis_range=[0, 100],
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)"
)
fig_share.update_yaxes(showgrid=True, gridwidth=0.5, gridcolor='#EDF2F7')
fig_share.update_xaxes(showgrid=False)

st.plotly_chart(fig_share, use_container_width=True)

st.divider()

# 3. 도시 유형별 상세 비교 (이후 내용 모두 유지)
st.subheader("🏠 도시 유형별 소비 특성 및 전력 불균형 분석")
city_comp = all_dy.merge(sector[["지역", "지역유형", "산업비중(%)"]], on="지역")

c1, c2 = st.columns(2)

with c1:
    # 기존 유지: 유형별 전력 사용 강도 비교
    st.write("**[유형별 일평균 전력 사용량]**")
    type_avg = city_comp.groupby("지역유형")["power_usage"].mean().reset_index()
    fig_type_bar = px.bar(type_avg, x="지역유형", y="power_usage", color="지역유형",
                          title="도시 유형별 전력 사용 강도 비교",
                          color_discrete_map={"공업도시형": "#0066cc", "주거/상업도시형": "#80ccff"})
    st.plotly_chart(fig_type_bar.update_layout(height=450), use_container_width=True)

with c2:
    # 기존 유지: 지역별 1인당 소비 vs 생산 불균형
    st.write("**[지역별 1인당 소비 vs 생산 불균형]**")
    pop_energy = get_pop_energy_data()
    
    if not pop_energy.empty:
        fig_bubble = px.scatter(
            pop_energy, x="1인당_전력소비량(MWh)", y="1인당_발전량(MWh)",
            color="자립도(%)", size="총인구수", hover_name="지역",
            color_continuous_scale="RdYlGn",
            labels={"1인당_전력소비량(MWh)": "소비(MWh)", "1인당_발전량(MWh)": "생산(MWh)"},
            title="1인당 전력 소비 및 발전량 분포"
        )
        # 자립 100% 기준선 추가
        max_val = max(pop_energy["1인당_전력소비량(MWh)"].max(), pop_energy["1인당_발전량(MWh)"].max())
        fig_bubble.add_shape(type="line", x0=0, y0=0, x1=max_val, y1=max_val, line=dict(color="red", dash="dash"))
        st.plotly_chart(fig_bubble.update_layout(height=450), use_container_width=True)
    else:
        st.info("발전량/인구 데이터를 로드할 수 없습니다.")

st.divider()