import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path

def get_path(f):
    candidates = [Path(f), Path("dataset")/f, Path("Project/dataset")/f, Path.cwd()/f, Path.cwd()/"dataset"/f]
    for p in candidates:
        if p.exists(): return str(p)
    raise FileNotFoundError(f"{f} 파일을 찾을 수 없습니다.")

def read_csv(f):
    path = get_path(f)
    for enc in ["utf-8-sig", "cp949", "euc-kr", "utf-8"]:
        try: return pd.read_csv(path, encoding=enc)
        except: continue

def norm_reg(n):
    if not isinstance(n, str): return n
    n = n.strip()
    mapping = {"서울":"서울특별시","부산":"부산광역시","대구":"대구광역시","인천":"인천광역시","광주":"광주광역시","대전":"대전광역시","울산":"울산광역시","세종":"세종특별자치시","경기":"경기도","강원":"강원도","충북":"충청북도","충남":"충청남도","전북":"전라북도","전남":"전라남도","경북":"경상북도","경남":"경상남도","제주":"제주특별자치도"}
    c2p = {"수원":"경기도","양평":"경기도","파주":"경기도","이천":"경기도","춘천":"강원도","강릉":"강원도","원주":"강원도","청주":"충청북도","홍성":"충청남도","전주":"전라북도","군산":"전라북도","목포":"전라남도","여수":"전라남도","창원":"경상남도","진주":"경상남도","안동":"경상북도","포항":"경상북도","구미":"경상북도","서귀포":"제주특별자치도"}
    return c2p.get(n, next((v for k,v in mapping.items() if k in n), n))

def to_num(s): return pd.to_numeric(s.astype(str).str.replace(",", ""), errors="coerce")

@st.cache_data
def load_all():
    p = read_csv("한국전력거래소_지역별 시간대별 전력거래량_2024.csv")
    p["지역"] = p["지역"].apply(norm_reg)
    p["거래일자"] = pd.to_datetime(p["거래일자"])
    p["거래일시"] = p["거래일자"] + pd.to_timedelta(p["거래시간"].astype(int)-1, unit="h")
    p["월"], p["시간"], p["요일번호"] = p["거래일시"].dt.month, p["거래일시"].dt.hour, p["거래일시"].dt.dayofweek
    p["요일"] = p["요일번호"].map({0: "월", 1: "화", 2: "수", 3: "목", 4: "금", 5: "토", 6: "일"})
    pdaily = p.groupby(["지역", "거래일자"])["전력거래량(MWh)"].sum().reset_index().rename(columns={"거래일자":"date", "전력거래량(MWh)":"power_usage"})

    w = read_csv("weather_data.csv").iloc[:, :6]
    w.columns = ["코드", "지점명", "일시", "temp", "강수량", "습도"]
    w["지역"], w["date"] = w["지점명"].apply(norm_reg), pd.to_datetime(w["일시"]).dt.normalize()
    for col in ["temp", "강수량", "습도"]: w[col] = to_num(w[col])
    wdaily = w.groupby(["지역", "date"]).agg({"temp":"mean", "강수량":"sum", "습도":"mean"}).reset_index()

    df = pd.merge(pdaily, wdaily, on=["지역", "date"])
    df["월"] = df["date"].dt.month
    df["CDD"], df["HDD"] = np.maximum(df["temp"]-24, 0), np.maximum(18-df["temp"], 0)
    df["rolling_mean_7"] = df.groupby("지역")["power_usage"].transform(lambda x: x.rolling(7, 1).mean())

    s_raw = read_csv("HOME_발전·판매_판매전력량_시도별용도별.csv").iloc[2:]
    s = pd.DataFrame({"지역": s_raw.iloc[:,0].apply(norm_reg), "주거용": to_num(s_raw.iloc[:,1]), "서비스업": to_num(s_raw.iloc[:,3]), "산업용": to_num(s_raw.iloc[:,33]), "합계": to_num(s_raw.iloc[:,34])}).dropna()
    s["산업비중(%)"], s["주거비중(%)"] = s["산업용"]/s["합계"]*100, s["주거용"]/s["합계"]*100
    s["지역유형"] = np.where(s["산업비중(%)"] >= 50, "공업도시형", "주거/상업도시형")

    sup = read_csv("발전량.csv")
    sup["date"] = pd.to_datetime(sup["년"].astype(str)+'-'+sup["월"].astype(str)+'-'+sup["일"].astype(str))
    sup["공급예비율(%)"] = to_num(sup["공급예비율(%)"])
    return p, df, s, sup

def sidebar_filters(power, daily):
    st.sidebar.header("필터 설정")
    reg_sel = st.sidebar.selectbox("지역 선택", sorted(power["지역"].unique()))
    h_rng = st.sidebar.slider("시간대 (0~23시)", 0, 23, (0, 23))
    d_rng = st.sidebar.date_input("날짜 범위 설정", [daily["date"].min(), daily["date"].max()])
    if len(d_rng) != 2: st.stop()
    return reg_sel, h_rng, d_rng