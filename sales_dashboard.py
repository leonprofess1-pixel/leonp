import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- 페이지 설정 (선택 사항) ---
st.set_page_config(page_title="Sales 부서 이직 분석", layout="wide")

# --- 데이터 로딩 및 캐싱 ---
@st.cache_data
def load_data(file_path):
    """지정된 경로에서 HR 데이터셋을 로드합니다."""
    # 1. 입력된 경로에서 시도
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    
    # 2. 파일명만 가지고 현재 디렉토리에서 시도 (경로 에러 방지용)
    filename = os.path.basename(file_path)
    if os.path.exists(filename):
        return pd.read_csv(filename)
        
    st.error(f"데이터 파일을 찾을 수 없습니다. 다음 경로를 확인해주세요: {file_path}")
    return None

# 데이터 로드 (경로가 정확한지 꼭 확인하세요)
# 만약 파일이 파이썬 파일과 같은 폴더에 있다면 'HR-Employee-Attrition.csv'로만 적어도 됩니다.
target_file_path = 'HR-employee-attrition/HR-Employee-Attrition.csv'
df_original = load_data(target_file_path)

if df_original is None:
    st.stop()

# --- Sales 부서 데이터 필터링 ---
df = df_original[df_original['Department'] == 'Sales'].copy()
df['Attrition_numeric'] = df['Attrition'].apply(lambda x: 1 if x == 'Yes' else 0)

if df.empty:
    st.error("Sales 부서에 대한 데이터를 찾을 수 없습니다.")
    st.stop()

# --- 사이드바 ---
st.sidebar.title("Sales 부서 심층 분석")

# 직무 선택
sales_job_roles = df['JobRole'].unique()
selected_job_roles = st.sidebar.multiselect(
    '직무 선택 (JobRole)',
    options=sales_job_roles,
    default=sales_job_roles
)

# 성별 선택
selected_gender = st.sidebar.radio(
    '성별 선택 (Gender)',
    options=['All'] + list(df['Gender'].unique()),
    index=0
)

# 연령대 선택
min_age, max_age = int(df['Age'].min()), int(df['Age'].max())
selected_age_range = st.sidebar.slider(
    '연령대 선택 (Age Range)',
    min_value=min_age,
    max_value=max_age,
    value=(min_age, max_age)
)

# 근속 년수 선택
min_years, max_years = int(df['YearsAtCompany'].min()), int(df['YearsAtCompany'].max())
selected_years_range = st.sidebar.slider(
    '근속 년수 선택 (Years at Company)',
    min_value=min_years,
    max_value=max_years,
    value=(min_years, max_years)
)


# --- 데이터 필터링 (사이드바 기반) ---
filtered_df = df[
    (df['JobRole'].isin(selected_job_roles)) &
    (df['Age'] >= selected_age_range[0]) &
    (df['Age'] <= selected_age_range[1]) &
    (df['YearsAtCompany'] >= selected_years_range[0]) &
    (df['YearsAtCompany'] <= selected_years_range[1])
]
if selected_gender != 'All':
    filtered_df = filtered_df[filtered_df['Gender'] == selected_gender]


# --- 메인 화면 ---
st.title("Sales 부서 이직 요인 심층 분석 대시보드")

if filtered_df.empty:
    st.warning("선택한 필터 조건에 해당하는 데이터가 없습니다.")
else:
    tab1, tab2, tab3 = st.tabs(["Sales 이직 현황", "핵심 이직 동인 분석", "결론 및 제언"])

    with tab1:
        st.header("Sales 부서 이직 현황 요약")

        # 주요 지표
        total_employees = filtered_df.shape[0]
        attrition_rate = filtered_df['Attrition_numeric'].mean() * 100
        avg_income = filtered_df['MonthlyIncome'].mean()
        avg_satisfaction = filtered_df['JobSatisfaction'].mean()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("총 직원 수", f"{total_employees:,}")
        col2.metric("이직률", f"{attrition_rate:.2f}%")
        col3.metric("평균 월소득", f"${avg_income:,.0f}")
        col4.metric("평균 직무 만족도", f"{avg_satisfaction:.2f}")

        st.divider()

        # 직무별 이직률
        st.subheader("Sales 직무별 이직률")
        job_attrition_rate = filtered_df.groupby('JobRole')['Attrition_numeric'].mean().reset_index()
        job_attrition_rate['Attrition_numeric'] *= 100
        fig_job_rate = px.bar(
            job_attrition_rate.sort_values(by='Attrition_numeric', ascending=False),
            x='JobRole',
            y='Attrition_numeric',
            text=job_attrition_rate['Attrition_numeric'].apply(lambda x: f'{x:.2f}%'),
            title='Sales 직무별 이직률 (%)'
        )
        st.plotly_chart(fig_job_rate, use_container_width=True)
        st.caption("Sales 부서 내에서 'Sales Representative'의 이직률이 'Sales Executive'보다 현저히 높은 경향을 보입니다.")

    with tab2:
        st.header("핵심 이직 동인 분석 (Sales 부서)")
        st.info("Sales 부서 직원들의 이직에 영향을 미치는 주요 요인을 분석합니다.")

        # 주요 이직 유발 요인 (OverTime, BusinessTravel)
        key_factors = ['OverTime', 'BusinessTravel', 'WorkLifeBalance']
        for factor in key_factors:
            factor_attrition_rate = filtered_df.groupby(factor)['Attrition_numeric'].mean().reset_index()
            factor_attrition_rate['Attrition_numeric'] *= 100
            
            fig = px.bar(
                factor_attrition_rate.sort_values(by='Attrition_numeric', ascending=False),
                x=factor,
                y='Attrition_numeric',
                title=f'{factor}에 따른 이직률 (%)',
                text=factor_attrition_rate['Attrition_numeric'].apply(lambda x: f'{x:.2f}%')
            )
            st.plotly_chart(fig, use_container_width=True)

        # 소득과 이직의 관계
        st.subheader("월소득과 이직의 관계")
        fig_income_box = px.box(filtered_df, x='Attrition', y='MonthlyIncome', 
                                title='이직 여부에 따른 월소득 분포', color='Attrition')
        st.plotly_chart(fig_income_box, use_container_width=True)
        st.caption("Sales 부서 내에서도 이직하는 직원 그룹의 월소득이 잔류 그룹보다 낮은 경향을 보입니다.")

        # 총 경력 대비 월소득 (경력 정체성 확인)
        st.subheader("총 경력과 월소득의 관계")
        
        # 주의: trendline='ols'는 statsmodels 라이브러리가 필요합니다.
        try:
            fig_scatter_income = px.scatter(
                filtered_df,
                x='TotalWorkingYears',
                y='MonthlyIncome',
                color='Attrition',
                trendline='ols', 
                title='총 경력 대비 월소득 분포 (이직 여부별)',
                labels={'TotalWorkingYears': '총 경력 (년)', 'MonthlyIncome': '월소득'}
            )
            st.plotly_chart(fig_scatter_income, use_container_width=True)
        except Exception as e:
            fig_scatter_income = px.scatter(
                filtered_df,
                x='TotalWorkingYears',
                y='MonthlyIncome',
                color='Attrition',
                title='총 경력 대비 월소득 분포 (이직 여부별)',
                labels={'TotalWorkingYears': '총 경력 (년)', 'MonthlyIncome': '월소득'}
            )
            st.plotly_chart(fig_scatter_income, use_container_width=True)
            
        st.caption("경력이 쌓여도 소득이 정체되거나 낮다고 느끼는 그룹에서 이직률이 높게 나타날 수 있습니다.")


    with tab3:
        st.header("결론 및 전략적 제언")
        st.subheader("Sales 부서 이직 요인 분석 결론")
        st.markdown("""
        - **결론 1: 'Sales Representative' 직무의 높은 이직률**
          - Sales 부서 내에서도 특히 'Sales Representative' 직무의 이직률이 매우 높게 나타납니다. 이는 해당 직무의 업무 강도, 보상 수준, 경력 개발 경로와 관련이 깊을 것으로 추정됩니다.

        - **결론 2: 초과근무와 잦은 출장이 핵심 동인**
          - 'OverTime'과 'BusinessTravel'은 Sales 부서의 이직률을 높이는 가장 결정적인 요인입니다. 특히 출장이 잦은(Travel_Frequently) 그룹의 이직률이 매우 높습니다.

        - **결론 3: 소득 불만족**
          - 이직하는 직원 그룹은 잔류하는 그룹에 비해 월소득 중앙값이 현저히 낮습니다. 이는 경력에 비해 보상이 충분하지 않다고 느끼는 직원들이 이탈할 가능성이 높다는 것을 시사합니다.
        """)

        st.subheader("인재 유지를 위한 전략적 제언")
        st.markdown("""
        - **1. 'Sales Representative' 직무 처우 개선 (단기)**
          - **목표:** 해당 직무의 높은 이탈률을 시급히 낮춥니다.
          - **실행 방안:**
            - 기본급 및 성과급(Commission) 구조를 재검토하여, 노력에 대한 공정한 보상이 이루어지도록 합니다.
            - 잦은 출장에 대한 현실적인 출장비 및 대체 휴무를 제공하여 워라밸을 개선합니다.

        - **2. 경력 개발 경로(CDP) 강화 (중기)**
          - **목표:** 'Sales Representative'가 'Sales Executive' 또는 다른 직무로 성장할 수 있는 명확한 비전을 제시합니다.
          - **실행 방안:**
            - 역량 기반의 승진 기준을 명확히 하고, 필요한 교육 및 멘토링 프로그램을 지원합니다.
            - 성공적인 경력 전환 사례를 공유하여 동기를 부여합니다.

        - **3. 워크로드 관리 및 조직 문화 개선 (장기)**
          - **목표:** 불필요한 초과근무를 줄이고, 일과 삶의 균형을 중시하는 문화를 정착시킵니다.
          - **실행 방안:**
            - 영업 관리 시스템(SFA)을 고도화하여 비효율적인 업무를 줄입니다.
            - 리더십 교육을 통해 관리자들이 팀원들의 워크로드를 효과적으로 관리하고, 건강한 피드백 문화를 조성하도록 합니다.
        """)
