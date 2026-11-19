import streamlit as st

st.set_page_config(
    page_title="BactoMut | TEM-1 Mutation Analysis",
    layout="wide",
)

pages = {
    "Home": st.Page("pages/0_Home.py", title="Home", default=True),
    "Analysis": st.Page(
        "pages/1_Mutation_Analysis.py", title="Mutation Analysis"
    ),
    "Prediction": st.Page("pages/2_AI_Prediction.py", title="AI Prediction"),
    "Dataset": st.Page("pages/3_Dataset_Explorer.py", title="Dataset Explorer"),
    "Models": st.Page("pages/4_Model_Performance.py", title="Model Performance"),
    "Report": st.Page("pages/5_Research_Report.py", title="Research Report"),
}
st.session_state["bactomut_pages"] = pages
navigation = st.navigation(list(pages.values()), position="hidden")
navigation.run()
