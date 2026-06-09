import streamlit as st
import pandas as pd
from fredapi import Fred
import plotly.graph_objects as go

# 1. 页面极简美化配置（适配手机端与PC端）
st.set_page_config(page_title="Wicksellian Spread Radar", layout="wide")
st.title("📊 Wicksellian Spread 高频监控看板")
st.subheader("用冷峻的数据，穿透全球宏观流动性迷雾")

# 2. 侧边栏：配置中心
st.sidebar.header("⚙️ 核心配置")
api_key = st.sidebar.text_input("输入你的 FRED API Key", type="password")
st.sidebar.markdown("""
[如何获取免费 API Key?](https://fredapi.stlouisfed.org/login/apikeys)
*注：本应用完全在本地/你指定的云端运行，不存储任何私钥。*
""")

if not api_key:
    st.info("💡 请在左侧侧边栏输入你的 FRED API Key 以激活实时数据流。")
    st.stop()

# 实例化 FRED 客户端
try:
    fred = Fred(api_key=api_key)
except Exception as e:
    st.error(f"API Key 验证失败，请检查输入。错误信息: {e}")
    st.stop()

# 3. 核心数据异步抓取与同频清洗引擎
@st.cache_data(ttl=3600)  # 缓存1小时，避免频繁请求被限流
def fetch_and_process_wicksellian_data():
    # 抓取原始序列
    # GDPC1: 实际GDP (季度) | BAA: 穆迪Baa企业债收益率 (日度) | CPIAUCSL: 核心CPI (月度)
    raw_gdp = fred.get_series('GDPC1')
    raw_baa = fred.get_series('BAA')
    raw_cpi = fred.get_series('CPIAUCSL')
    
    # 转换为 DataFrame 并统一时间轴
    df_gdp = pd.DataFrame(raw_gdp, columns=['gdp_raw'])
    df_baa = pd.DataFrame(raw_baa, columns=['baa_nominal'])
    df_cpi = pd.DataFrame(raw_cpi, columns=['cpi_raw'])
    
    # 计算同比变动率 (%)
    df_gdp['gdp_yoy'] = df_gdp['gdp_raw'].pct_change(periods=4) * 100 # 季度数据同比看去年同期(4个季度)
    df_cpi['cpi_yoy'] = df_cpi['cpi_raw'].pct_change(periods=12) * 100 # 月度数据同比看去年同期(12个月)
    
    # 将所有数据合并到一个以“天”为单位的主时间轴上，并进行前向填充（Forward Fill）
    # 这样可以用每天最新的债券收益率，动态对撞最新的宏观基本面
    master_df = df_baa.join(df_cpi['cpi_yoy'], how='left').join(df_gdp['gdp_yoy'], how='left')
    master_df.ffill(inplace=True)
    master_df.dropna(inplace=True)
    
    # 核心维克塞尔逻辑公式计算
    master_df['real_cost_of_capital'] = master_df['baa_nominal'] - master_df['cpi_yoy']
    master_df['wicksellian_spread'] = master_df['gdp_yoy'] - master_df['real_cost_of_capital']
    
    return master_df

with st.spinner("正在破译 FRED 数据库，对齐宏观多米诺骨牌..."):
    data = fetch_and_process_wicksellian_data()

# 4. 提取最新核心硬数据
latest_row = data.iloc[-1]
latest_date = data.index[-1].strftime('%Y-%m-%d')
spread_val = latest_row['wicksellian_spread']
gdp_val = latest_row['gdp_yoy']
cost_val = latest_row['real_cost_of_capital']

# 5. 顶层大数仪表盘 (Metrics)
col1, col2, col3 = st.columns(3)
with col1:
    # 动态风险颜色对齐
    if spread_val > 0:
        st.metric(label="维克塞尔利差 (Wicksellian Spread)", value=f"{spread_val:.2f}%", delta="安全区间")
    else:
        st.metric(label="维克塞尔利差 (Wicksellian Spread)", value=f"{spread_val:.2f}%", delta="触发清算警报", delta_color="inverse")
with col2:
    st.metric(label="内生经济增速 (Real GDP YoY 影子值)", value=f"{gdp_val:.2f}%")
with col3:
    st.metric(label="真实资本成本 (Real Cost of Capital)", value=f"{cost_val:.2f}%")

st.caption(f"📊 数据源自圣路易斯联储 | 最后一笔高频对齐更新时间: {latest_date}")

# 6. 高级趋势可视化 (Plotly 交互式图表)
st.write("---")
st.subheader("📈 维克塞尔利差历史长周期演变 (2000 - 至今)")

fig = go.Figure()

# 绘制利差主体曲线
fig.add_trace(go.Scatter(
    x=data.index, y=data['wicksellian_spread'],
    mode='lines', name='Wicksellian Spread Proxy',
    line=dict(color='#2b5c8f', width=2.5)
))

# 绘制零轴（生死线）
fig.add_shape(
    type="line", x0=data.index[0], y0=0, x1=data.index[-1], y1=0,
    line=dict(color="Red", width=1.5, dash="dash")
)

fig.update_layout(
    xaxis_title="年份",
    yaxis_title="利差权重 (%)",
    hovermode="x unified",
    template="plotly_white",
    margin=dict(l=20, r=20, t=20, b=20)
)

st.plotly_chart(fig, use_container_width=True)

# 7. 军师暗房：自动化风暴推演
st.write("---")
st.subheader("🕵️ 独行者的反向推演逻辑仓")

if spread_val > 0:
    st.success(f"**当前沙盘诊断**：维克塞尔利差仍保持在 **{spread_val:.2f}%** 的正向盈余状态。这意味着虽然外部风暴（日元清算）在敲打衍生品外围，但实体企业的回报仍能覆盖实际债务利息。**策略：高位科技链条在清算期属于‘情绪面错杀’，持币死盯红利资产补跌，准备在跌透后拿麻袋装带血的硬科技筹码。**")
else:
    st.sidebar.error("🚨 警告：维克塞尔利差已正式转负！")
    st.error("**当前沙盘诊断**：危险！指标已跌破零轴。说明实体经济增速已经无法承载当前的实际利率成本。信用周期步入强制崩塌期。**策略：无条件防守，全面清空一切高β风险资产，全球流动性无差别踩踏即将进入最惨烈阶段。**")
