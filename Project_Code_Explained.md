# NutriZone (NutriTwin) - Project Structure & File Guide

This document provides a comprehensive, easy-to-understand breakdown of every major folder and file in the NutriZone project. This is your "map" to how the entire system works together.

---

## 1. Root Directory (The Essentials)
These files act as the starting point for your entire application.

*   **`server.py`**: The **most important file**. This is the FastAPI backend server. It serves the 3D frontend, handles API requests, and connects the user interface to the AI logic. You run the app using this file (`python server.py`).
*   **`requirements.txt`**: The shopping list of Python packages (like `fastapi`, `uvicorn`, `torch`) needed to run this project.
*   **`.venv/` & `__pycache__/`**: System folders. `.venv` holds your installed Python libraries, and `__pycache__` makes Python run faster. *(Do not manually edit these).*

---

## 2. `/frontend` (The 3D User Interface)
This folder contains the custom, glassmorphic 3D web application.

*   **`index.html`**: The main webpage structure. It holds the navigation bars, the hidden side-panels, and the `<canvas>` where the 3D organs are drawn.
*   **`styles.css`**: Contains all the visual design code—including the glowing neon effects, glass-like panels, and animations.
*   **`app.js`**: The frontend manager. It boots up the 3D scene, handles tab-switching between the Meal Planner and AI Insights, and starts polling the server for health data.
*   **`/modules/`**: Contains the specific JavaScript logic blocks:
    *   `SceneManager.js / OrganManager.js / AnimationController.js`: These handle the actual rendering, lighting, breathing animations, and color-changing of the 3D (.glb) models.
    *   `MealPlannerUI.js / SimulationUI.js / UIController.js`: These grab the text you type into the panels and send it to the Python backend.
    *   `DataService.js`: Constantly "listens" to the backend to see if organ health has changed.

---

## 3. `/api` (The Backend Endpoints)
These files create the "URLs" that the frontend talks to.

*   **`routes.py`**: Handles requests for the Meal Planner. When you click "Generate Plan," this file catches the request and triggers the Orchestrator.
*   **`simulation.py`**: Handles requests from the "Feed Twin" module. It manages feeding nutrients to the simulation and requesting insights from the AI.
*   **`body_state.py`**: A continuous endpoint (`/body-state`) that simply reports the current mathematical health score of every organ so the 3D UI knows what color to draw them.

---

## 4. `/agents` (The Rule-Based "Science" Brain)
These files use strict math and rules to design safe meal plans.

*   **`orchestrator.py`**: The "Manager". It takes your profile, calculates your exact metabolic needs, queries the database, and puts the final meal plan together.
*   **`user_profile_agent.py`**: Calculates your Body Mass Index (BMI), Basal Metabolic Rate (BMR), and Total Daily Energy Expenditure (TDEE).
*   **`meal_planner_agent.py`**: Applies medical constraints (e.g., "If patient has PCOS, restrict carbs to <40%").
*   **`llm_explanation_agent.py`**: Wraps the final meal plan in a nice, human-readable text explanation.

---

## 5. `/simulation` (The AI & Bio "Art" Brain)
*(Formerly named 'stimulation')*. This is the complex Deep Learning and Biological Simulation engine.

*   **`organ_twin.py`**: The actual mathematical simulation. If you feed the twin 50 grams of sugar, this file contains the math that calculates how much stress that puts on the pancreas and liver.
*   **`dqn_agent.py`**: The Reinforcement Learning (RL) agent. It plays a "game" trying to figure out the best sequence of meals to maximize organ health.
*   **`llm_explainer.py`**: Connects to your local **Ollama (BioMistral)** model. It translates raw math (e.g., "-0.05 heart health") into clinical medical explanations. 
*   **`llm_reward_shaper.py`**: Has the medical LLM "grade" the RL agent's food choices to teach it safe nutrition.
*   **`llm_sensitivity_calibrator.py`**: Adjusts how sensitive the 3D organs are based on your diseases.
*   **`config.py`**: Holds hardcoded constants to define what a "Healthy" organ baseline is vs. a "Sick" baseline.

---

## 6. `/database` & `/data` (The Knowledge Base)
The memory storage for actual food recipes and their nutrients.

*   **`/data/processed/nutrition.db`**: A local SQLite database containing real food items (like Indian dishes) and their exact macros (protein, carbs, sodium, sugar, etc.).
*   **`/database/queries.py`**: The SQL logic. When the AI says "Give me 10 high-protein, low-sugar meals", this file reaches into `nutrition.db` to pull them out.
*   **`/database/load_csv_to_sqlite.py`**: A helper script you used to convert raw CSV spreadsheets into your working `.db` file.

---

## 7. `/llm` (The External Cloud AI)
*   **`llama_loader.py`**: Unlike BioMistral (which runs locally via Ollama for the simulations), this file connects to **Groq's Cloud API (Llama 3)**. It is specifically used to write the friendly conversational summaries at the bottom of the Meal Planner.

---

## 8. `/organs` (The 3D Assets)
*   This folder contains `.glb` files. These are 3D model files (like Heart, Liver, Kidneys, Muscles) created in external software like Blender and rendered dynamically by your frontend.

---

### Unused/Deprecated Folders
*You can safely ignore or delete these folders as they are no longer actively used by the core NutriZone application:*
*   `/config`, `/retrieval`, `/rl`, `/rules_engine`, `/scripts`, `/tests`, `/utils`
*   `app.py` & `main.py` (Old Streamlit versions of the UI)
