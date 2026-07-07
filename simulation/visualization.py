import plotly.graph_objects as go
import plotly.express as px

def create_health_trend_chart(history_data, title="Health Trend"):
    """Create a health trend chart from history data"""
    if not history_data:
        return None
    
    df = pd.DataFrame(history_data)
    if df.empty:
        return None
    
    fig = px.line(df, x='timestamp', y='health', title=title)
    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="Health Score",
        hovermode='x unified'
    )
    return fig

def create_nutrient_radar_chart(nutrients, title="Nutrient Profile"):
    """Create a radar chart for nutrient profile"""
    categories = list(nutrients.keys())
    values = list(nutrients.values())
    
    fig = go.Figure(data=go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, max(values) * 1.2]
            )),
        showlegend=False,
        title=title
    )
    
    return fig