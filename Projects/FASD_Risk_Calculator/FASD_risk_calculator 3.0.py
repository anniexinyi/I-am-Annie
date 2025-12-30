import streamlit as st

# --- 0. PAGE CONFIGURATION (Must be first) ---
st.set_page_config(page_title="Prenatal Risk Assessor", page_icon="👶")

# --- 1. PASSWORD PROTECTION SYSTEM ---
def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == "123456":
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store password
        else:
            st.session_state["password_correct"] = False

    # Initialize session state for password
    if "password_correct" not in st.session_state:
        # First run, show input
        st.text_input(
            "Please enter the access code to use this tool:", 
            type="password", 
            on_change=password_entered, 
            key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # Password incorrect, show input again
        st.text_input(
            "Incorrect code. Please try again:", 
            type="password", 
            on_change=password_entered, 
            key="password"
        )
        st.error("😕 Password incorrect")
        return False
    else:
        # Password correct
        return True

# --- 2. CALCULATOR LOGIC ---
def calculate_risk(inputs):
    """
    Analyzes inputs and returns: (score_out_of_10, color, message_text)
    """
    raw_score = 0
    
    # --- Logic: Maternal History ---
    if inputs['q5'] == "Currently a regular drinker": 
        raw_score += 40
    elif inputs['q5'] == "Less than 3 months ago": 
        raw_score += 25
    elif inputs['q5'] == "3 to 12 months ago": 
        raw_score += 10
        
    if inputs['q4'] == "Yes": 
        raw_score += 20
        
    if inputs['q6'] == "No, I need help": 
        raw_score += 20
    elif inputs['q6'] == "Unsure / Difficult": 
        raw_score += 10
        
    # --- Logic: Partner Influence ---
    if inputs['q8'] == "Heavy (15+ drinks)": 
        raw_score += 10
    elif inputs['q8'] == "Moderate (8–14 drinks)": 
        raw_score += 5
        
    # --- Logic: Medical & BMI ---
    if inputs['q9'] == "Yes": 
        raw_score += 5
    # if inputs['q10']: # If list is not empty
    #     raw_score += 5
    if inputs['q10']:  # list 非空
        if len(inputs['q10']) == 1:
            raw_score += 5     # 单一物质（烟草 或 THC）
        else:
            raw_score += 10
        
    # BMI Risk (Underweight is risky for fetal development)
    if inputs['bmi'] > 0 and inputs['bmi'] < 18.5: 
        raw_score += 5

    # Cap raw score at 100, normalize to 1-10
    raw_score = min(raw_score, 100)
    final_score_10 = max(1.0, round(raw_score / 10.0, 1))
    
    # Determine Status Color
    if raw_score <= 33:
        color = "green"
        label = "Low Risk"
    elif raw_score <= 64:
        color = "yellow"
        label = "Moderate Risk"
    else:
        color = "red"
        label = "High Risk"

    return final_score_10, color, label

# --- 3. MAIN APP INTERFACE ---
if check_password():
    # Everything indented here only runs IF password is correct
    
    # Logout Button
    if st.button("Log out"):
        del st.session_state["password_correct"]
        st.rerun()

    st.title("👶 Prenatal Risk Assessment Tool")
    
    st.info(
        "**Instructions:** Please answer all questions honestly. "
        "Your data is processed locally and is not saved."
    )
    
    st.warning("⚠️ **Medical Disclaimer:** This tool is for educational prototyping only. It is not a medical diagnosis.")

    st.markdown("---")

    # --- SECTION A: BIOMETRICS (Vertical Fill-in-Blank) ---
    st.header("Section A: Biometrics")
    st.write("Please fill in the blanks below:")
    sex = st.radio("Q1. What is your Sex?", ["Female", "Male"])

    # We set value=0 to make it look like a blank form
    h = st.number_input("Q1. What is your Height (cm)?", min_value=0, max_value=250, value=0)
    w = st.number_input("Q2. What is your Weight (kg)?", min_value=0, max_value=300, value=0)
    a = st.number_input("Q3. What is your Age?", min_value=0, max_value=100, value=0)

    # Calculate BMI instantly for display (only if height is entered)
    bmi = 0.0
    if h > 0:
        bmi = round(w / ((h/100)**2), 2)
        st.caption(f"Calculated BMI: {bmi}")

    st.markdown("---")

    # --- SECTION B: MATERNAL HISTORY ---
    st.header("Section B: Maternal History")
    
    q4 = st.radio(
        "Q4. In the past 12 months, have you been diagnosed with Alcohol Use Disorder?", 
        ["No", "Yes"]
    )
    
    q5 = st.selectbox(
        "Q5. When were you last a “regular drinker” (at least 1 drink/week)?", 
        [
            "More than 1 year ago / Never", 
            "3 to 12 months ago", 
            "Less than 3 months ago", 
            "Currently a regular drinker"
        ]
    )
    
    q6 = st.radio(
        "Q6. Do you believe you can stop drinking entirely while trying to conceive?", 
        ["Yes, definitely", "Unsure / Difficult", "No, I need help"]
    )

    # --- SECTION C: PARTNER ---
    st.header("Section C: Partner Influence")
    
    q7 = st.radio("Q7. Does your partner drink alcohol?", ["No / No Partner", "Yes"])
    
    q8 = "N/A"
    if q7 == "Yes":
        q8 = st.selectbox(
            "Q8. Approximately how many drinks does your partner consume per week?", 
            ["Light (1–7 drinks)", "Moderate (8–14 drinks)", "Heavy (15+ drinks)"]
        )

    # --- SECTION D: MEDICAL ---
    st.header("Section D: Medical & Lifestyle")
    
    q9 = st.radio(
        "Q9. Do you take medications that interact with alcohol (e.g., SSRIs)?", 
        ["No", "Yes"]
    )
    
    q10 = st.multiselect(
        "Q10. Do you use other substances? (Select all that apply)", 
        ["Tobacco/Nicotine", "THC/Cannabis"]
    )

    st.markdown("---")

    # --- CALCULATION TRIGGER ---
    if st.button("Calculate Risk Analysis", type="primary"):
        # Validation: Check if they filled out Section A
        if h == 0 or w == 0:
            st.error("❗ Please fill out your Height and Weight in Section A before calculating.")
        else:
            # Package inputs
            data = {
                'bmi': bmi, 
                'q4': q4, 
                'q5': q5, 
                'q6': q6, 
                'q8': q8, 
                'q9': q9, 
                'q10': q10
            }
            
            # Run Logic
            score, color, txt = calculate_risk(data)
            
            # Display Results
            st.divider()
            st.subheader("Analysis Result")
            
            # Use columns for a nice scorecard look
            col1, col2 = st.columns(2)
            col1.metric("Risk Score", f"{score}/10")
            col2.metric("BMI Status", f"{bmi}")
            
            if color == "green":
                st.success(f"**Status: {txt}**\n\nNo significant risk factors identified. Continue maintaining a healthy lifestyle.")
            elif color == "yellow":
                st.warning(
                    f"**Status: {txt}**\n\n"
                    "**Precaution Advised.** Your answers indicate environmental or behavioral factors that increase risk. "
                    "Consider discussing lifestyle changes or 'dry house' rules with your partner."
                )
            else:
                st.error(
                    f"**Status: {txt}**\n\n"
                    "**Action Required.** Your profile suggests a high probability of risk factors associated with FASD. "
                    "Please speak with an OB-GYN or addiction specialist immediately."
                )