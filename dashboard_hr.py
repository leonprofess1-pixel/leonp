import streamlit as st
import pandas as pd
import plotly.express as px

# --- 데이터 로딩 및 캐싱 ---
@st.cache_data
def load_data(file_path):
    """지정된 경로에서 HR 데이터셋을 로드합니다."""
    try:
        return pd.read_csv(file_path)
    except FileNotFoundError:
        st.error(f"데이터 파일을 찾을 수 없습니다: {file_path}")
        return None

df = load_data('HR-employee-attrition/HR-Employee-Attrition.csv')

if df is None:
    st.stop()

# 'Attrition'을 숫자로 변환 (Yes=1, No=0)
df['Attrition_numeric'] = df['Attrition'].apply(lambda x: 1 if x == 'Yes' else 0)

# --- 사이드바 ---
st.sidebar.title("HR 이직률 감소를 위한 분석 대시보드")

# 부서 선택
selected_departments = st.sidebar.multiselect(
    '부서 선택 (Department)',
    options=df['Department'].unique(),
    default=df['Department'].unique()
)

# 직무 선택
selected_job_roles = st.sidebar.multiselect(
    '직무 선택 (JobRole)',
    options=df['JobRole'].unique(),
    default=df['JobRole'].unique()
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


# --- 데이터 필터링 ---
filtered_df = df[
    (df['Department'].isin(selected_departments)) &
    (df['JobRole'].isin(selected_job_roles)) &
    (df['Age'] >= selected_age_range[0]) &
    (df['Age'] <= selected_age_range[1])
]
if selected_gender != 'All':
    filtered_df = filtered_df[filtered_df['Gender'] == selected_gender]


# --- 메인 화면 ---
st.title("HR 직원 이직 분석 및 개선 방안 대시보드")

if filtered_df.empty:
    st.warning("선택한 필터 조건에 해당하는 데이터가 없습니다.")
else:
    tab1, tab2, tab3 = st.tabs(["대시보드 요약", "상세 이직률 분석", "이직 핵심 요인 분석"])

    with tab1:
        st.header("대시보드 요약 (Dashboard Summary)")

        # 주요 지표
        total_employees = filtered_df.shape[0]
        attrition_rate = filtered_df['Attrition_numeric'].mean() * 100
        avg_satisfaction = filtered_df['JobSatisfaction'].mean()
        avg_income = filtered_df['MonthlyIncome'].mean()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("총 직원 수", f"{total_employees:,}")
        col2.metric("전체 이직률", f"{attrition_rate:.2f}%")
        col3.metric("평균 직무 만족도", f"{avg_satisfaction:.2f}")
        col4.metric("평균 월소득", f"${avg_income:,.0f}")

        # 전체 이직 현황
        st.subheader("전체 이직 현황")
        attrition_counts = filtered_df['Attrition'].value_counts().reset_index()
        fig_pie = px.pie(attrition_counts, values='count', names='Attrition', title='이직자/잔류자 비율', hole=0.3)
        st.plotly_chart(fig_pie)

        # 부서별 이직률
        st.subheader("부서별 이직률")
        dept_attrition_rate = filtered_df.groupby('Department')['Attrition_numeric'].mean().reset_index()
        dept_attrition_rate['Attrition_numeric'] *= 100
        fig_dept_rate = px.bar(
            dept_attrition_rate.sort_values(by='Attrition_numeric', ascending=False),
            x='Department',
            y='Attrition_numeric',
            text=dept_attrition_rate['Attrition_numeric'].apply(lambda x: f'{x:.2f}%'),
            title='부서별 이직률 (%)'
        )
        st.plotly_chart(fig_dept_rate)


    with tab2:
        st.header("상세 이직률 분석 (Detailed Attrition Rate Analysis)")

        # 인구통계별 이직률
        st.subheader("인구통계별 이직률")
        bins = [18, 30, 40, 50, 60]
        labels = ['18-29', '30-39', '40-49', '50-59']
        filtered_df['AgeGroup'] = pd.cut(filtered_df['Age'], bins=bins, labels=labels, right=False)
        age_attrition_rate = filtered_df.groupby('AgeGroup', observed=True)['Attrition_numeric'].mean().reset_index()
        age_attrition_rate['Attrition_numeric'] *= 100
        fig_age_rate = px.bar(age_attrition_rate, x='AgeGroup', y='Attrition_numeric', title='연령대별 이직률 (%)')
        st.plotly_chart(fig_age_rate)
        
        # 성별 및 결혼 상태별 이직률
        fig_sunburst = px.sunburst(
            filtered_df,
            path=['Gender', 'MaritalStatus', 'Attrition'],
            title='성별 및 결혼 상태에 따른 이직 현황'
        )
        st.plotly_chart(fig_sunburst)

        # 직무 관련 특성별 이직률
        st.subheader("직무 관련 특성별 이직률")
        job_level_satisfaction = filtered_df.groupby(['JobLevel', 'JobSatisfaction'])['Attrition_numeric'].mean().reset_index()
        job_level_satisfaction['size'] = filtered_df.groupby(['JobLevel', 'JobSatisfaction']).size().values
        fig_treemap = px.treemap(
            job_level_satisfaction,
            path=[px.Constant("전체"), 'JobLevel', 'JobSatisfaction'],
            values='size',
            color='Attrition_numeric',
            hover_data={'Attrition_numeric': ':.2%'},
            color_continuous_scale='RdYlGn_r',
            title='직무 등급 및 만족도별 이직률'
        )
        st.plotly_chart(fig_treemap)

        # 근속 년수 그룹별 이직률
        bins_years = [0, 3, 6, 11, df['YearsAtCompany'].max() + 1]
        labels_years = ['0-2년', '3-5년', '6-10년', '11년 이상']
        filtered_df['YearsGroup'] = pd.cut(filtered_df['YearsAtCompany'], bins=bins_years, labels=labels_years, right=False)
        years_attrition_rate = filtered_df.groupby('YearsGroup', observed=True)['Attrition_numeric'].mean().reset_index()
        years_attrition_rate['Attrition_numeric'] *= 100
        fig_years_rate = px.bar(years_attrition_rate, x='YearsGroup', y='Attrition_numeric', title='근속 년수 그룹별 이직률 (%)')
        st.plotly_chart(fig_years_rate)

    with tab3:
        st.header("이직 핵심 요인 분석 (Key Driver Analysis)")
        st.info('"어떻게 하면 이직률을 낮출 수 있을까?"에 대한 데이터 기반 답변을 제공합니다.')

        # 주요 이직 유발 요인 시각화
        st.subheader("주요 이직 유발 요인")
        key_factors = ['OverTime', 'BusinessTravel', 'WorkLifeBalance']
        for factor in key_factors:
            factor_attrition_rate = filtered_df.groupby(factor)['Attrition_numeric'].mean().reset_index()
            factor_attrition_rate['Attrition_numeric'] *= 100
            
            fig = px.bar(
                factor_attrition_rate,
                x=factor,
                y='Attrition_numeric',
                title=f'{factor}에 따른 이직률 (%)',
                text=factor_attrition_rate['Attrition_numeric'].apply(lambda x: f'{x:.2f}%')
            )
            st.plotly_chart(fig)
            
            if factor == 'OverTime':
                ot_yes_rate = factor_attrition_rate[factor_attrition_rate['OverTime'] == 'Yes']['Attrition_numeric'].iloc[0]
                ot_no_rate = factor_attrition_rate[factor_attrition_rate['OverTime'] == 'No']['Attrition_numeric'].iloc[0]
                if ot_no_rate > 0:
                    st.caption(f"초과근무 'Yes' 그룹의 이직률이 'No' 그룹보다 약 {ot_yes_rate/ot_no_rate:.1f}배 높습니다.")

        # 소득과 이직의 관계
        st.subheader("소득과 이직의 관계")
        fig_income_box = px.box(filtered_df, x='Attrition', y='MonthlyIncome', title='이직 여부에 따른 월소득 분포')
        st.plotly_chart(fig_income_box)
        st.caption("이직 그룹(Yes)의 월소득 중앙값이 잔류 그룹(No)보다 낮은 경향을 보입니다.")

        # 분석 결론 및 제언
        st.subheader("분석 결론 및 제언")
        st.markdown("""
        - **결론:** 초과 근무, 잦은 출장, 낮은 직무 만족도는 이직률을 높이는 핵심 요인으로 파악됩니다. 특히, 20대 후반 ~ 30대 초반의 저연차 직원 그룹에서 이러한 경향이 두드러집니다. 또한 이직하는 직원 그룹은 잔류하는 그룹에 비해 평균 월소득이 낮은 경향을 보입니다.

        - **제언:**
          1.  **초과근무 관리:** 초과 근무 보상 체계를 현실화하고, 워크로드 분산을 위한 인력 재배치 또는 충원을 고려해야 합니다.
          2.  **출장 정책 개선:** 잦은 출장이 필요한 직무에 대해 재택 근무 옵션을 확대하거나, 출장 관련 복지를 강화하여 만족도를 높일 수 있습니다.
          3.  **경력 초기 직원 지원:** 신입 및 저연차 직원을 위한 멘토링 프로그램을 강화하고, 명확한 경력 개발 경로를 제시하여 직무 만족도와 조직 몰입도를 향상시켜야 합니다.
          4.  **보상 체계 점검:** 경쟁력 있는 급여 수준을 유지하고, 성과에 따른 공정한 보상 시스템을 구축하여 소득 불만으로 인한 이직을 최소화해야 합니다.
        """)