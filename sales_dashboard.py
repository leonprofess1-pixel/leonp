import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# --- 1. 데이터 준비 및 보조 함수 ---

@st.cache_data
def load_data(file_path):
    """데이터를 로드하고 기본 전처리 수행"""
    df = pd.read_csv(file_path)
    
    # Attrition을 0/1로 변환
    df['Attrition_Numeric'] = df['Attrition'].apply(lambda x: 1 if x == 'Yes' else 0)
    
    # 연령 그룹화
    bins_age = [18, 30, 40, 50, 60]
    labels_age = ['20s', '30s', '40s', '50s+']
    # Age_Group 생성 시, bins의 범위를 닫는 방법(right=False)에 따라 29세가 '20s'에 포함됨.
    df['Age_Group'] = pd.cut(df['Age'], bins=bins_age, labels=labels_age, right=False)
    
    # 근속 년수 그룹화
    bins_years = [-1, 2, 5, 10, df['YearsAtCompany'].max() + 1]
    labels_years = ['0-2 Years', '3-5 Years', '6-10 Years', '11+ Years']
    df['YearsAtCompany_Group'] = pd.cut(df['YearsAtCompany'], bins=bins_years, labels=labels_years, right=False)
    
    return df

def calculate_attrition_rate(df):
    """필터링된 데이터프레임의 이직률(%) 계산 (DataFrame 입력용)"""
    if df.empty or len(df) == 0:
        return 0.0
    # 이 함수는 필터링된 DF 전체를 입력으로 받을 때만 사용됩니다.
    attrition_rate = (df['Attrition_Numeric'].sum() / len(df)) * 100
    return attrition_rate

def create_rate_bar_chart(df, column, title):
    """특정 컬럼별 이직률 바 차트 생성"""
    if df.empty:
        return None
        
    attrition_summary = df.groupby(column, observed=False)['Attrition_Numeric'].agg(
        total='count',
        attrition_count='sum'
    ).reset_index()
    attrition_summary['Attrition Rate (%)'] = (attrition_summary['attrition_count'] / attrition_summary['total']) * 100

    # plotly 차트 생성
    fig = px.bar(
        attrition_summary.sort_values(by='Attrition Rate (%)', ascending=False),
        x=column,
        y='Attrition Rate (%)',
        color='Attrition Rate (%)',
        text='Attrition Rate (%)',
        color_continuous_scale=px.colors.sequential.Reds,
        title=f'<b>{title}</b>'
    )
    fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    fig.update_layout(xaxis_title=column, yaxis_title="Attrition Rate (%)", uniformtext_minsize=8, uniformtext_mode='hide')
    return fig

# 데이터 로드
df = load_data('HR-employee-attrition/HR-Employee-Attrition.csv')

# --- 2. 사이드바 (Sidebar) 필터 ---
st.set_page_config(layout="wide")
st.sidebar.title("HR 이직률 감소를 위한 분석 대시보드")

# 필터 옵션
all_departments = df['Department'].unique().tolist()
selected_departments = st.sidebar.multiselect(
    "부서 (Department)",
    options=all_departments,
    default=all_departments
)

all_job_roles = df[df['Department'].isin(selected_departments)]['JobRole'].unique().tolist()
selected_job_roles = st.sidebar.multiselect(
    "직무 (JobRole)",
    options=all_job_roles,
    default=all_job_roles
)

selected_gender = st.sidebar.radio(
    "성별 (Gender)",
    options=['All', 'Male', 'Female'],
    index=0
)

min_age, max_age = int(df['Age'].min()), int(df['Age'].max())
selected_age_range = st.sidebar.slider(
    "연령대 (Age Range)",
    min_value=min_age,
    max_value=max_age,
    value=(min_age, max_age)
)

# 데이터 필터링 적용
filtered_df = df[
    (df['Department'].isin(selected_departments)) &
    (df['JobRole'].isin(selected_job_roles)) &
    (df['Age'] >= selected_age_range[0]) &
    (df['Age'] <= selected_age_range[1])
]
if selected_gender != 'All':
    filtered_df = filtered_df[filtered_df['Gender'] == selected_gender]

# --- 3. 메인 화면 - 탭 구조 ---
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    ["대시보드 요약", "상세 이직률 분석", "이직 핵심 요인 분석", "🎯 Sales팀 심층 분석", "데이터 검색 및 탐색", "Raw Data"]
)

# --- Tab 1: 대시보드 요약 (Dashboard Summary) ---
with tab1:
    st.header("핵심 지표")
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_employees = len(filtered_df)
    total_attrition_rate = calculate_attrition_rate(filtered_df)
    avg_job_satisfaction = filtered_df['JobSatisfaction'].mean() if not filtered_df.empty else 0
    avg_monthly_income = filtered_df['MonthlyIncome'].mean() if not filtered_df.empty else 0
    
    col1.metric("총 직원 수", f"{total_employees:,}")
    col2.metric("전체 이직률 (%)", f"{total_attrition_rate:.2f}%")
    col3.metric("평균 직무 만족도 (1-4)", f"{avg_job_satisfaction:.2f}")
    col4.metric("평균 월소득", f"${avg_monthly_income:,.0f}")
    
    st.markdown("---")
    
    st.header("전체 이직 현황")
    
    col_l, col_r = st.columns(2)
    
    with col_l:
        st.subheader("이직자/잔류자 비율")
        if not filtered_df.empty:
            fig_pie = px.pie(
                filtered_df, 
                names='Attrition', 
                title='<b>전체 이직자(Yes)/잔류자(No) 비율</b>',
                color_discrete_sequence=px.colors.sequential.RdBu
            )
            st.plotly_chart(fig_pie, width='stretch')
        else:
            st.warning("필터링된 데이터가 없습니다.")

    with col_r:
        st.subheader("부서별 이직률")
        fig_dept_rate = create_rate_bar_chart(filtered_df, 'Department', '부서별 이직률')
        if fig_dept_rate:
            st.plotly_chart(fig_dept_rate, width='stretch')
        else:
            st.warning("필터링된 데이터가 없습니다.")

# --- Tab 2: 상세 이직률 분석 (Detailed Attrition Rate Analysis) ---
with tab2:
    st.header("인구통계별 이직률")
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.subheader("연령대별 이직률")
        fig_age = create_rate_bar_chart(filtered_df, 'Age_Group', '연령대별 이직률')
        if fig_age:
            st.plotly_chart(fig_age, width='stretch')
            st.info("💡 20대(20s) 그룹의 이직률이 가장 높습니다.")
        else:
            st.warning("필터링된 데이터가 없습니다.")

    with col_b:
        st.subheader("성별 및 결혼 상태별 이직률")
        if not filtered_df.empty:
            # 선버스트 차트: 성별 -> 결혼 상태 -> 이직
            df_sunburst = filtered_df.groupby(['Gender', 'MaritalStatus', 'Attrition_Numeric'], observed=False).size().reset_index(name='Count')
            df_sunburst['Attrition_Label'] = df_sunburst['Attrition_Numeric'].apply(lambda x: 'Leaver' if x == 1 else 'Stay')
            
            fig_sunburst = px.sunburst(
                df_sunburst,
                path=['Gender', 'MaritalStatus', 'Attrition_Label'],
                values='Count',
                color='Attrition_Label',
                color_discrete_map={'Stay': 'blue', 'Leaver': 'red'},
                title='<b>성별 및 결혼 상태별 이직 현황 (Leaver Count)</b>'
            )
            fig_sunburst.update_layout(margin=dict(t=30, l=0, r=0, b=0))
            st.plotly_chart(fig_sunburst, width='stretch')
        else:
            st.warning("필터링된 데이터가 없습니다.")

    st.markdown("---")
    st.header("직무 관련 특성별 이직률")

    col_c, col_d = st.columns(2)

    with col_c:
        st.subheader("직무 등급 및 만족도별 이직률")
        if not filtered_df.empty:
            # *********** 오류 수정 부분 ***********
            # Treemap: JobLevel -> JobSatisfaction (색상: 이직률)
            # calculate_attrition_rate 대신 lambda 함수를 사용하여 집계 오류 해결
            df_treemap = filtered_df.groupby(['JobLevel', 'JobSatisfaction'], observed=False)['Attrition_Numeric'].agg(
                total='count',
                # s는 Attrition_Numeric Series for each group
                attrition_rate=lambda s: (s.sum() / len(s)) * 100 if len(s) > 0 else 0 
            ).reset_index()
            # **************************************
            
            fig_treemap = px.treemap(
                df_treemap,
                path=['JobLevel', 'JobSatisfaction'],
                values='total',
                color='attrition_rate',
                color_continuous_scale='Plasma',
                title='<b>직무 등급 및 만족도별 직원 수 (색상: 이직률)</b>'
            )
            st.plotly_chart(fig_treemap, width='stretch')
            st.caption("JobLevel이 낮고 JobSatisfaction이 낮은 영역일수록 이직률(색상)이 높습니다.")
        else:
            st.warning("필터링된 데이터가 없습니다.")


    with col_d:
        st.subheader("근속 년수 그룹별 이직률")
        fig_years = create_rate_bar_chart(filtered_df, 'YearsAtCompany_Group', '근속 년수 그룹별 이직률')
        if fig_years:
            st.plotly_chart(fig_years, width='stretch')
            st.info("💡 입사 2년 미만(0-2 Years) 그룹의 이직률이 가장 높게 나타납니다.")
        else:
            st.warning("필터링된 데이터가 없습니다.")


# --- Tab 3: 이직 핵심 요인 분석 (Key Driver Analysis) ---
with tab3:
    st.header("주요 이직 유발 요인 시각화")
    
    # 핵심 변수 선정
    key_drivers = ['OverTime', 'BusinessTravel', 'WorkLifeBalance']
    
    for driver in key_drivers:
        st.subheader(f"{driver}별 이직률")
        fig_driver = create_rate_bar_chart(filtered_df, driver, f'{driver} 그룹별 이직률')
        if fig_driver:
            st.plotly_chart(fig_driver, width='stretch')
            
            if driver == 'OverTime':
                if not filtered_df.empty:
                    ot_yes = filtered_df[filtered_df['OverTime'] == 'Yes']
                    ot_no = filtered_df[filtered_df['OverTime'] == 'No']
                    
                    rate_yes = calculate_attrition_rate(ot_yes)
                    rate_no = calculate_attrition_rate(ot_no)
                    
                    if rate_no > 0:
                         st.info(f"🚨 **초과 근무('Yes') 그룹의 이직률({rate_yes:.1f}%)**은 **비초과 근무 그룹({rate_no:.1f}%)**보다 약 **{(rate_yes/rate_no):.1f}배** 높습니다. 초과 근무는 이직의 강력한 요인입니다.")
        else:
            st.warning("필터링된 데이터가 없습니다.")

            
    st.markdown("---")
    st.header("소득과 이직의 관계")
    
    if not filtered_df.empty:
        fig_income = px.box(
            filtered_df,
            x="Attrition",
            y="MonthlyIncome",
            color="Attrition",
            title="<b>이직 그룹(Yes/No)별 월소득 분포</b>",
            color_discrete_map={'Yes': 'red', 'No': 'green'}
        )
        st.plotly_chart(fig_income, width='stretch')
        st.caption("이직자 그룹(Yes)의 월소득 분포가 잔류자 그룹(No)보다 낮게 형성되어, 저소득층의 이직 경향이 뚜렷합니다.")
    else:
        st.warning("필터링된 데이터가 없습니다.")


# --- Tab 4: 🎯 Sales팀 심층 분석 (Sales Attrition Deep Dive) ---
with tab4:
    st.title("🎯 Sales팀 이직률 심층 분석: 10가지 핵심 요인")
    
    # Sales팀 데이터만 필터링 (전체 데이터 기준)
    df_sales = df[df['Department'] == 'Sales']
    
    if df_sales.empty:
        st.error("Sales 부서 데이터가 없습니다. (전체 데이터 기준)")
    else:
        # A. Sales팀 핵심 지표 및 현황
        st.header("Sales팀 핵심 성과 지표")
        
        col1, col2, col3, col4 = st.columns(4)
        
        sales_total = len(df_sales)
        sales_attrition_rate = calculate_attrition_rate(df_sales)
        sales_avg_income = df_sales['MonthlyIncome'].mean()
        sales_avg_years = df_sales['YearsAtCompany'].mean()
        
        col1.metric("Sales팀 총 직원 수", f"{sales_total:,}")
        col2.metric("Sales팀 이직률 (%)", f"{sales_attrition_rate:.2f}%")
        col3.metric("평균 월소득", f"${sales_avg_income:,.0f}")
        col4.metric("평균 잔류 년수", f"{sales_avg_years:.1f}년")
        
        st.markdown("---")
        
        # Sales팀 이직 비율 파이 차트
        st.subheader("Sales팀 이직자/잔류자 비율")
        fig_sales_pie = px.pie(
            df_sales, 
            names='Attrition', 
            title='<b>Sales팀 전체 이직자(Yes)/잔류자(No) 비율</b>',
            color_discrete_sequence=px.colors.sequential.RdBu
        )
        st.plotly_chart(fig_sales_pie, width='stretch')
        
        st.markdown("---")
        
        # B. Sales팀 이직에 영향을 미치는 10가지 핵심 요인 분석
        st.header("Sales팀 이직률에 영향을 미치는 10가지 핵심 요인")

        # 1. 초과 근무 (OverTime)
        st.subheader("1. 초과 근무 (OverTime)별 이직률")
        fig_ot_sales = create_rate_bar_chart(df_sales, 'OverTime', 'Sales팀 OverTime 그룹별 이직률')
        st.plotly_chart(fig_ot_sales, width='stretch')

        # 2. 월 소득 (MonthlyIncome) 분포
        st.subheader("2. 월 소득 (MonthlyIncome) 분포")
        fig_income_sales = px.box(
            df_sales,
            x="Attrition",
            y="MonthlyIncome",
            color="Attrition",
            title="<b>Sales팀 이직 그룹(Yes/No)별 월소득 분포</b>",
            color_discrete_map={'Yes': 'red', 'No': 'green'}
        )
        st.plotly_chart(fig_income_sales, width='stretch')
        st.caption("Sales팀 이직자 그룹의 월소득 중간값(Median)이 잔류자보다 명확히 낮습니다.")

        # 3. 출장 빈도 (BusinessTravel)
        st.subheader("3. 출장 빈도 (BusinessTravel)별 이직률")
        fig_bt_sales = create_rate_bar_chart(df_sales, 'BusinessTravel', 'Sales팀 BusinessTravel 그룹별 이직률')
        st.plotly_chart(fig_bt_sales, width='stretch')
        st.caption("출장이 잦은 ('Travel_Frequently') Sales 직원의 이직률이 높습니다.")
        
        # 4. 직무 만족도 (JobSatisfaction)
        st.subheader("4. 직무 만족도 (JobSatisfaction)별 이직률")
        fig_js_sales = create_rate_bar_chart(df_sales, 'JobSatisfaction', 'Sales팀 JobSatisfaction 그룹별 이직률')
        st.plotly_chart(fig_js_sales, width='stretch')
        
        # 5. 근속 년수 (YearsAtCompany) 그룹
        st.subheader("5. 근속 년수 (YearsAtCompany) 그룹별 이직률")
        fig_yac_sales = create_rate_bar_chart(df_sales, 'YearsAtCompany_Group', 'Sales팀 YearsAtCompany 그룹별 이직률')
        st.plotly_chart(fig_yac_sales, width='stretch')
        
        # 6. 재택 거리 (DistanceFromHome)
        st.subheader("6. 재택 거리 (DistanceFromHome) 분포")
        fig_dfh_sales = px.box(
            df_sales,
            x="Attrition",
            y="DistanceFromHome",
            color="Attrition",
            title="<b>Sales팀 이직 그룹(Yes/No)별 재택 거리 (km) 분포</b>",
            color_discrete_map={'Yes': 'red', 'No': 'green'}
        )
        st.plotly_chart(fig_dfh_sales, width='stretch')
        
        # 7. 마지막 승진 후 년수 (YearsSinceLastPromotion)
        st.subheader("7. 마지막 승진 후 년수 (YearsSinceLastPromotion)별 이직률")
        
        # 승진 후 년수 그룹화 (0년, 1-2년, 3-5년, 6년 이상)
        bins_promo = [-1, 0, 2, 5, df_sales['YearsSinceLastPromotion'].max() + 1]
        labels_promo = ['0 Years', '1-2 Years', '3-5 Years', '6+ Years']
        
        # df_sales에만 임시 컬럼 생성
        df_sales.loc[:, 'Promo_Group'] = pd.cut(df_sales['YearsSinceLastPromotion'], bins=bins_promo, labels=labels_promo, right=False)
        
        fig_promo_sales = create_rate_bar_chart(df_sales, 'Promo_Group', 'Sales팀 마지막 승진 후 년수 그룹별 이직률')
        st.plotly_chart(fig_promo_sales, width='stretch')
        st.caption("승진이 오래된 그룹일수록 이직률이 높아지는 경향이 있습니다.")
        
        # 8. 업무/삶의 균형 (WorkLifeBalance)
        st.subheader("8. 업무/삶의 균형 (WorkLifeBalance)별 이직률")
        fig_wlb_sales = create_rate_bar_chart(df_sales, 'WorkLifeBalance', 'Sales팀 WorkLifeBalance 그룹별 이직률')
        st.plotly_chart(fig_wlb_sales, width='stretch')

        # 9. 회사 근무 경력 (TotalWorkingYears)
        st.subheader("9. 회사 근무 경력 (TotalWorkingYears) 분포")
        fig_twy_sales = px.box(
            df_sales,
            x="Attrition",
            y="TotalWorkingYears",
            color="Attrition",
            title="<b>Sales팀 이직 그룹(Yes/No)별 총 근무 경력 분포</b>",
            color_discrete_map={'Yes': 'red', 'No': 'green'}
        )
        st.plotly_chart(fig_twy_sales, width='stretch')

        # 10. 직무 등급 (JobLevel)
        st.subheader("10. 직무 등급 (JobLevel)별 이직률")
        fig_jl_sales = create_rate_bar_chart(df_sales, 'JobLevel', 'Sales팀 JobLevel 그룹별 이직률')
        st.plotly_chart(fig_jl_sales, width='stretch')
        
        st.markdown("---")
        
        # C. Sales팀 맞춤형 분석 결론 및 제언
        st.header("🔑 Sales팀 맞춤형 분석 결론 및 제언")
        
        st.markdown(
            """
            ### **결론: Sales팀 이직의 주된 교차점**
            Sales 부서의 이직은 단순히 하나의 요인이 아닌, **낮은 월 소득, 잦은 초과 근무, 그리고 낮은 직무 등급(JobLevel 1, 2)이 결합**될 때 그 위험이 폭발적으로 증가합니다. 
            특히 **입사 2년 미만 주니어 직원**이 이직 위험군에 속하며, 이는 이들이 경쟁력 있는 보상이나 명확한 경력 성장 경로를 찾지 못하고 있음을 강력히 시사합니다.
            """
        )
        
        st.warning("### Sales팀 이직률 감소를 위한 특화된 3가지 제언")
        st.markdown(
            """
            1.  **💰 보상 경쟁력 확보 (월 소득 개선):** 이직자 그룹의 월 소득 하위 25% 지점을 벤치마킹하여, 해당 수준의 직원들에게 **경쟁력 있는 인센티브 또는 커미션 보너스 구조**를 신속하게 재설계하여 이직을 방지해야 합니다.
            2.  **💼 경력 성장 경로 명확화 (Job Level & 승진):** 주니어 직원을 위한 **명확한 승진 경로(Job Level Up 로드맵)**를 제시하고, 마지막 승진 후 3년 이상 된 직원들을 대상으로 **경력 개발 면담**을 의무화해야 합니다.
            3.  **⚖️ 워크로드 및 문화 개선 (OverTime & Travel):** 초과 근무를 유발하는 비효율적인 프로세스를 점검하고, 출장이 잦은 직원을 대상으로 **추가적인 보상 또는 유연 근무 옵션**을 제공하여 워크-라이프 밸런스 점수를 개선해야 합니다.
            """
        )

# --- Tab 5: 데이터 검색 및 탐색 (Data Search & Explore) ---
with tab5:
    st.header("데이터 검색 및 탐색")
    st.info("다양한 키워드로 데이터를 검색하고 결과를 확인할 수 있습니다.")

    search_query = st.text_input("검색어를 입력하세요 (예: Sales, Male, 2000)")

    if search_query:
        # 문자열 컬럼만 검색 대상으로 지정
        string_columns = filtered_df.select_dtypes(include='object').columns
        
        # 검색어 포함 여부 확인
        search_results = filtered_df[
            filtered_df[string_columns].apply(
                lambda column: column.str.contains(search_query, case=False, na=False)
            ).any(axis=1)
        ]
        
        if not search_results.empty:
            st.subheader(f"'{search_query}' 검색 결과 ({len(search_results)}건)")
            st.dataframe(search_results)
        else:
            st.warning(f"'{search_query}'에 해당하는 검색 결과가 없습니다.")
    else:
        st.info("검색어를 입력하시면 필터링된 데이터 내에서 관련 정보를 찾을 수 있습니다.")

# --- Tab 6: Raw Data ---
with tab6:
    st.header("Raw Data")
    st.info("현재 필터링된 전체 데이터입니다.")
    if not filtered_df.empty:
        st.dataframe(filtered_df)
    else:
        st.warning("필터링된 데이터가 없습니다.")
