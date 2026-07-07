import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from simulation.config import ORGAN_BASELINES

def render_tabs():
    """Render the main content tabs"""
    tab1, tab2, tab3, tab4 = st.tabs([
        " 3D Digital Twin", 
        " Organ Analytics", 
        " AI Insights", 
        " LLM Explanations"
    ])
    
    # TAB 1: 3D Digital Twin
    with tab1:
        render_3d_twin_tab()
    
    # TAB 2: Organ Analytics
    with tab2:
        render_organ_analytics_tab()
    
    # TAB 3: AI Insights
    with tab3:
        render_ai_insights_tab()
    
    # TAB 4: LLM Explanations
    with tab4:
        render_llm_explanations_tab()

def render_3d_twin_tab():
    """Render the 3D Digital Twin tab"""
    st.header("🧬 Real-time 3D Digital Twin")
    
    # Create 3D visualization
    fig = st.session_state.digital_twin.create_3d_visualization()
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    # Health summary
    overall_health = st.session_state.digital_twin.get_overall_health()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Overall Health", f"{overall_health:.1%}")
    with col2:
        st.metric("Total Meals", len(st.session_state.meal_history))
    with col3:
        st.metric("Last Reward", f"{st.session_state.last_reward:.3f}")
    with col4:
        critical_organs = sum(1 for org in st.session_state.digital_twin.organs.values() 
                             if org["health"] < 0.6)
        st.metric("At Risk Organs", critical_organs, 
                 delta="-" if critical_organs == 0 else f"+{critical_organs}")
    
    # Organ health grid
    st.subheader(" Organ Health Status")
    organs = sorted(st.session_state.digital_twin.organs.keys())
    cols = st.columns(5)  # Adjusted for 10 organs
    
    for idx, organ_name in enumerate(organs):
        with cols[idx % 5]:
            organ = st.session_state.digital_twin.organs[organ_name]
            health_pct = organ["health"] * 100
            
            st.markdown(f"""
            <div style='text-align:center; padding:10px; margin:5px; 
                         background:{organ['color']}20; border-radius:10px; 
                         border:2px solid {organ['color']}'>
                <div style='font-size:12px; font-weight:bold; color:#e0e0e0'>{organ_name.title()}</div>
                <div style='font-size:20px; font-weight:bold; color:{organ["color"]}'>
                    {health_pct:.0f}%
                </div>
                <div style='font-size:10px; color:#999'>{organ['system'][:15]}...</div>
            </div>
            """, unsafe_allow_html=True)

def render_organ_analytics_tab():
    """Render the Organ Analytics tab"""
    st.header(" Detailed Organ Analytics")
    
    # Select organ for detailed view
    selected_organ = st.selectbox(
        "Select Organ for Detailed Analysis",
        sorted(st.session_state.digital_twin.organs.keys()),
        format_func=lambda x: x.title(),
        key="organ_select"
    )
    
    if selected_organ:
        organ = st.session_state.digital_twin.organs[selected_organ]
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            # Organ info card
            st.markdown(f"""
            <div style='padding:20px; background:rgba(30,30,50,0.8); border-radius:10px; border-left:4px solid {organ["color"]}'>
                <h4 style='color:#ffffff'>{selected_organ.title()}</h4>
                <p style='color:#e0e0e0'><b style='color:#ffffff'>System:</b> {organ['system']}</p>
                <p style='color:#e0e0e0'><b style='color:#ffffff'>Function:</b> {organ['function']}</p>
                <p style='color:#e0e0e0'><b style='color:#ffffff'>Risk Factors:</b> {', '.join(organ['risk_factors'])}</p>
                <p style='color:#e0e0e0'><b style='color:#ffffff'>Sensitive to:</b> {', '.join(list(organ['sensitivity'].keys())[:3])}...</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Health trend
            if st.session_state.digital_twin.history[selected_organ]:
                history_data = list(st.session_state.digital_twin.history[selected_organ])
                if history_data:
                    trend_df = pd.DataFrame(history_data)
                    
                    if not trend_df.empty and 'timestamp' in trend_df.columns and 'health' in trend_df.columns:
                        fig_trend = px.line(trend_df, x="timestamp", y="health",
                                          title=f"{selected_organ.title()} Health Trend")
                        st.plotly_chart(fig_trend, use_container_width=True)
        
        with col2:
            # Metrics dashboard
            st.subheader(" Performance Metrics")
            
            metrics = organ["metrics"]
            metric_cols = st.columns(2)
            
            for idx, (metric_name, metric_value) in enumerate(metrics.items()):
                with metric_cols[idx % 2]:
                    # Get baseline for comparison
                    baseline = ORGAN_BASELINES.get(selected_organ, {}).get(metric_name, 100)
                    deviation = ((metric_value - baseline) / baseline) * 100
                    
                    # Color code based on deviation
                    if abs(deviation) < 10:
                        color = "green"
                    elif abs(deviation) < 25:
                        color = "orange"
                    else:
                        color = "red"
                    
                    st.markdown(f"""
                    <div style='padding:15px; margin:5px; background:rgba(30,30,50,0.8); border-radius:8px; border-left:4px solid {color}'>
                        <div style='font-size:12px; color:#aaa'>{metric_name.replace('_', ' ').title()}</div>
                        <div style='font-size:20px; font-weight:bold; color:{color}'>{metric_value:.1f}</div>
                        <div style='font-size:10px; color:#999'>Baseline: {baseline:.1f} ({deviation:+.1f}%)</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Nutrient sensitivity visualization
            st.subheader(" Nutrient Sensitivity")
            sensitivities = organ["sensitivity"]
            
            if sensitivities:
                # Create bar chart
                fig_sensitivity = go.Figure(data=[
                    go.Bar(
                        x=list(sensitivities.keys()),
                        y=list(sensitivities.values()),
                        marker_color=['red' if v > 0 else 'green' for v in sensitivities.values()],
                        text=[f"{v:+.2f}" for v in sensitivities.values()],
                        textposition='auto'
                    )
                ])
                
                fig_sensitivity.update_layout(
                    title="Impact of Nutrients (Positive = Harmful, Negative = Beneficial)",
                    yaxis_title="Impact Coefficient",
                    height=300
                )
                st.plotly_chart(fig_sensitivity, use_container_width=True)

def render_ai_insights_tab():
    """Render the AI Insights tab"""
    st.header(" DQN Agent Insights")
    
    if st.session_state.meal_history:
        # Latest recommendation
        latest_meal = st.session_state.meal_history[-1]
        
        st.markdown(f"""
        <div style='padding:20px; background:rgba(30,40,60,0.9); border-radius:10px; border-left:5px solid #4ECDC4'>
            <h3 style='color:#ffffff'>Latest AI Recommendation</h3>
            <p style='font-size:18px; margin:10px 0; color:#e0e0e0'>{latest_meal['recommendation']}</p>
            <p style='color:#bbbbbb'><small>Action: {latest_meal.get('action', 'N/A')} | Reward: {latest_meal.get('reward', 0):.3f} | Health Δ: {latest_meal.get('health_change', 0):+.3f}</small></p>
            <small style='color:#999999'>Based on analysis of {len(st.session_state.meal_history)} meals</small>
        </div>
        """, unsafe_allow_html=True)
        
        # Agent learning progress
        st.subheader(" DQN Learning Progress")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Exploration Rate", f"{st.session_state.dqn_agent.epsilon:.3f}")
        with col2:
            st.metric("Memory Size", len(st.session_state.dqn_agent.memory))
        with col3:
            st.metric("Decisions Made", len(st.session_state.dqn_agent.decision_log))
        with col4:
            avg_reward = np.mean([m.get('reward', 0) for m in st.session_state.meal_history[-5:]]) if st.session_state.meal_history else 0
            st.metric("Avg Reward (last 5)", f"{avg_reward:.3f}")
        
        # Training loss chart
        if st.session_state.training_loss_history:
            st.subheader(" Training Loss Over Time")
            loss_df = pd.DataFrame({
                'Step': range(len(st.session_state.training_loss_history)),
                'Loss': st.session_state.training_loss_history
            })
            fig_loss = px.line(loss_df, x='Step', y='Loss', 
                             title='DQN Training Loss (Lower is Better)')
            st.plotly_chart(fig_loss, use_container_width=True)
        
        # Decision history
        if st.session_state.dqn_agent.decision_log:
            st.subheader(" Recent Decisions")
            
            recent_decisions = st.session_state.dqn_agent.decision_log[-8:]
            for decision in reversed(recent_decisions):
                q_display = f"Q: {decision.get('q_value', 0):.3f}" if decision.get('q_value') is not None else "Exploration"
                st.markdown(f"""
                <div style='padding:10px; margin:5px 0; background:rgba(30,30,50,0.8); border-radius:5px; border-left:3px solid #4ECDC4'>
                    <b style='color:#ffffff'>{decision['action']}</b><br>
                    <small style='color:#aaaaaa'>Time: {decision['timestamp'].strftime('%H:%M')} | {q_display} | ε: {decision['epsilon']:.3f}</small>
                </div>
                """, unsafe_allow_html=True)
        
        # Action distribution
        st.subheader(" Action Distribution")
        if st.session_state.dqn_agent.decision_log:
            action_counts = {}
            for decision in st.session_state.dqn_agent.decision_log:
                action = decision['action']
                action_counts[action] = action_counts.get(action, 0) + 1
            
            action_df = pd.DataFrame({
                'Action': list(action_counts.keys()),
                'Count': list(action_counts.values())
            }).sort_values('Count', ascending=False)
            
            fig_actions = px.bar(action_df, x='Action', y='Count', 
                               title='Frequency of AI Recommendations')
            fig_actions.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_actions, use_container_width=True)
    
    else:
        st.info("Simulate some meals to see AI insights!")

def render_llm_explanations_tab():
    """Render the LLM Explanations tab"""
    st.header(" LLM Medical Explanations")
    
    use_ollama = st.session_state.get("use_ollama", True)
    if not use_ollama:
        st.warning("Ollama LLM is disabled. Enable it in settings to get detailed explanations.")
    
    if st.session_state.explanations:
        # Filter buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            show_organ = st.checkbox("Show Organ Explanations", True, key="show_organ_tab4")
        with col2:
            show_agent = st.checkbox("Show Agent Explanations", True, key="show_agent_tab4")
        with col3:
            limit = st.slider("Show last N explanations", 1, 10, 3, key="limit_exp")
        
        # Show filtered explanations
        filtered_explanations = []
        for exp in st.session_state.explanations[-limit*2:]:  # Get more, then filter
            if exp.get("type") == "agent_decision" and show_agent:
                filtered_explanations.append(exp)
            elif exp.get("organ") and show_organ:
                filtered_explanations.append(exp)
        
        # Display filtered explanations
        for explanation in reversed(filtered_explanations[-limit:]):
            if explanation.get("type") == "agent_decision":
                reward_display = f" | Reward: {explanation.get('reward', 0):.3f}" if explanation.get('reward') is not None else ""
                st.markdown(f"""
                <div style='padding:20px; background:rgba(25,40,60,0.9); border-radius:10px; margin:10px 0; border-left:5px solid #45B7D1'>
                    <h4 style='color:#ffffff'> AI Decision Explanation{reward_display}</h4>
                    <div style='background:rgba(20,25,40,0.9); padding:15px; border-radius:5px; margin:10px 0; color:#e0e0e0'>
                        {explanation['explanation']}
                    </div>
                    <small style='color:#999999'>{explanation['timestamp'].strftime('%H:%M:%S')}</small>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style='padding:20px; background:rgba(25,45,35,0.9); border-radius:10px; margin:10px 0; border-left:5px solid #96CEB4'>
                    <h4 style='color:#ffffff'> {explanation['organ'].title()} Response Analysis</h4>
                    <div style='background:rgba(20,25,40,0.9); padding:15px; border-radius:5px; margin:10px 0; color:#e0e0e0'>
                        {explanation['explanation']}
                    </div>
                    <small style='color:#999999'>{explanation['timestamp'].strftime('%H:%M:%S')}</small>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No LLM explanations yet. Simulate a meal with Ollama enabled to get detailed explanations.")