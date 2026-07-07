import streamlit as st
from simulation.config import DEFAULT_NUTRIENTS

def render_sidebar(default_nutrients):
    """Render the sidebar with input controls"""
    st.sidebar.header(" Feed Your Digital Twin")
    st.sidebar.markdown("Enter exact nutrition values for this meal")
    
    sidebar_data = {
        "simulate_clicked": False,
        "train_clicked": False,
        "reset_clicked": False
    }
    
    with st.sidebar.expander(" Nutrition Inputs", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            calories = st.number_input("Calories", 0.0, 10000.0, default_nutrients['calories'], 10.0, key="cal")
            carbs = st.number_input("Carbs (g)", 0.0, 1000.0, default_nutrients['carbs'], 1.0, key="carbs")
            protein = st.number_input("Protein (g)", 0.0, 500.0, default_nutrients['protein'], 1.0, key="prot")
            fat = st.number_input("Fat (g)", 0.0, 500.0, default_nutrients['fat'], 1.0, key="fat")
        
        with col2:
            sugar = st.number_input("Sugar (g)", 0.0, 500.0, default_nutrients['sugar'], 0.5, key="sugar")
            fiber = st.number_input("Fiber (g)", 0.0, 200.0, default_nutrients['fiber'], 0.5, key="fiber")
            sodium = st.number_input("Sodium (mg)", 0.0, 25000.0, default_nutrients['sodium'], 10.0, key="sodium")
            calcium = st.number_input("Calcium (mg)", 0.0, 5000.0, default_nutrients['calcium'], 10.0, key="calc")
            iron = st.number_input("Iron (mg)", 0.0, 200.0, default_nutrients['iron'], 0.1, key="iron")
    
    with st.sidebar.expander(" Simulation Settings", expanded=True):
        meal_name = st.text_input("Meal Name", "My Meal", key="meal_name")
        use_ollama = st.checkbox("Use Ollama LLM", True, key="use_ollama")
        show_explanations = st.checkbox("Show Detailed Explanations", True, key="show_exp")
        auto_apply_ai = st.checkbox("Auto-apply AI recommendations", False, 
                                   help="Automatically modify nutrients based on AI suggestions")
    
    # Main buttons
    col_btn1, col_btn2, col_btn3 = st.sidebar.columns(3)
    with col_btn1:
        if st.button(" Simulate Meal", use_container_width=True, key="simulate"):
            sidebar_data["simulate_clicked"] = True
    
    with col_btn2:
        if st.button("Reset Twin", use_container_width=True, key="reset"):
            sidebar_data["reset_clicked"] = True
    
    with col_btn3:
        if st.button(" Train Agent", use_container_width=True, key="train"):
            sidebar_data["train_clicked"] = True
    
    # Store sidebar data
    sidebar_data.update({
        "nutrients": {
            'calories': calories,
            'carbs': carbs,
            'protein': protein,
            'fat': fat,
            'sugar': sugar,
            'fiber': fiber,
            'sodium': sodium,
            'calcium': calcium,
            'iron': iron
        },
        "meal_name": meal_name,
        "use_ollama": use_ollama,
        "show_explanations": show_explanations,
        "auto_apply_ai": auto_apply_ai
    })
    
    return sidebar_data
