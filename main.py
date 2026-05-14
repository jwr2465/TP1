import streamlit as st
from utils import load_all

# 0. 페이지 설정 (레이아웃을 wide로 설정하여 시원하게 보이게 함)
st.set_page_config(
    page_title="2024 전력 & 기상 데이터 분석 대시보드",
    page_icon="⚡",
    layout="wide"
)

# 1. 데이터 미리 로드 (캐싱 활용)
try:
    power, daily, sector, supply = load_all()
    data_loaded = True
except Exception as e:
    st.error(f"데이터 파일을 로드하는 중 오류가 발생했습니다: {e}")
    data_loaded = False

# 2. 메인 화면 구성
st.title("⚡ 2024 지역별 전력 사용량 & 기상 데이터 통합 분석")
st.markdown("---")

st.markdown("""
### 🔍 대시보드 개요
본 대시보드는 **2024년 대한민국 지역별 전력 거래량**과 **기상청 기상 데이터**를 결합하여, 기온 변화와 도시의 산업적 특성이 전력 수요에 미치는 영향을 분석합니다.

### 📂 분석 메뉴 안내 (좌측 사이드바에서 선택)
1. **📊 전체 전력 데이터**: 선택한 지역의 시간대별, 일별 전력 사용 패턴과 지도를 통한 전국 분포를 확인합니다.
2. **🌡️ 기온관련 데이터**: 기온, 강수량, 습도와 전력량의 상관관계를 분석하고, 냉난방 부하(CDD/HDD)를 살펴봅니다.
3. **🏭 주거환경 관련 데이터**: 도시의 산업 비중에 따른 전력 사용 패턴 차이와 지역별 총 사용량 순위를 비교합니다.
4. **⚡ 전력 수급 및 예비율 분석**: 전국 전력 공급 예비율 추이를 확인하고, 예비율이 가장 낮았던 날의 부하 패턴을 분석합니다.

### 🛠️ 데이터 출처
* 전력 데이터: 한국전력거래소 (지역별 시간대별 전력거래량)
* 기상 데이터: 기상청 공공데이터포털
* 용도별 데이터: 한국전력공사 (시도별 용도별 판매전력량)
""")

if data_loaded:
    st.success("✅ 모든 데이터가 성공적으로 로드되었습니다. 왼쪽 메뉴를 클릭하여 분석을 시작하세요!")
    
    # 간단한 요약 정보 표시
    st.info(f"현재 분석 대상 기간: **{daily['date'].min().date()} ~ {daily['date'].max().date()}**")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("대상 지역 수", f"{len(power['지역'].unique())}개 시/도")
    col2.metric("총 데이터 행수 (전력)", f"{len(power):,}개")
    col3.metric("총 데이터 행수 (기상)", f"{len(daily):,}개")
else:
    st.warning("⚠️ 데이터 파일이 검색되지 않습니다. `dataset/` 폴더에 CSV 파일이 있는지 확인해 주세요.")

st.sidebar.info("위 메뉴에서 페이지를 이동하세요.")