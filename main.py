import streamlit as st
import requests
from datetime import datetime

# Set page config
st.set_page_config(
    page_title="Plant Doctor 🌱",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Modern, clean CSS with improved styling
st.markdown("""
    <style>
    /* Modern background with dynamic gradient */
    .stApp {
        background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 25%, #a7f3d0 50%, #6ee7b7 100%);
        background-attachment: fixed;
    }
    
    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Aggressively hide all Streamlit alert/info/warning boxes */
    .stAlert, .stWarning, .stInfo, .stSuccess, .stError {
        display: none !important;
    }
    
    /* Hide empty divs and containers */
    div.element-container:empty {
        display: none !important;
    }
    
    /* Hide stale empty blocks */
    .stMarkdown:empty {
        display: none !important;
    }
    
    /* Remove extra padding */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Main header with glassmorphism effect */
    .main-header {
        text-align: center;
        padding: 3rem 2rem;
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 28px;
        margin-bottom: 2.5rem;
        box-shadow: 0 20px 60px rgba(5, 150, 105, 0.15);
        border: 1px solid rgba(255, 255, 255, 0.5);
        position: relative;
        overflow: hidden;
    }
    
    .main-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 6px;
        background: linear-gradient(90deg, #10b981, #059669, #047857, #059669, #10b981);
        background-size: 200% 100%;
        animation: shimmer 3s ease-in-out infinite;
    }
    
    @keyframes shimmer {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }
    
    .main-header h1 {
        color: #059669;
        font-size: 3.2rem;
        margin-bottom: 0.8rem;
        font-weight: 900;
        letter-spacing: -0.5px;
        text-shadow: none;
    }
    
    .main-header p {
        color: #047857;
        font-size: 1.3rem;
        margin: 0;
        font-weight: 600;
    }
    
    /* Mode selection card with hover effect */
    .mode-card {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        padding: 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        box-shadow: 0 8px 24px rgba(0,0,0,0.08);
        border: 1px solid rgba(255, 255, 255, 0.5);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .mode-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 32px rgba(5, 150, 105, 0.15);
    }
    
    .mode-card h3 {
        color: #059669;
        font-size: 1.5rem;
        margin-bottom: 1.2rem;
        font-weight: 800;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    /* Upload section with modern card design */
    .upload-section {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        padding: 2.5rem;
        border-radius: 24px;
        box-shadow: 0 12px 32px rgba(0,0,0,0.1);
        margin-bottom: 2rem;
        border: 1px solid rgba(255, 255, 255, 0.5);
        transition: all 0.3s ease;
    }
    
    .upload-section:hover {
        box-shadow: 0 16px 40px rgba(5, 150, 105, 0.15);
    }
    
    .upload-section h3 {
        color: #047857;
        font-size: 1.7rem;
        margin-bottom: 0.8rem;
        font-weight: 800;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    /* Result card - modern glassmorphism */
    .result-box {
        background: rgba(255, 255, 255, 0.98);
        backdrop-filter: blur(12px);
        padding: 2.5rem;
        border-radius: 28px;
        margin-top: 2rem;
        box-shadow: 0 20px 60px rgba(0,0,0,0.12);
        border: 1px solid rgba(255, 255, 255, 0.6);
        position: relative;
        overflow: hidden;
    }
    
    .result-box::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #10b981, #059669, #047857);
    }
    
    /* Hide any empty containers within result box */
    .result-box > div:empty,
    .result-box .element-container:empty,
    .result-box .stMarkdown:empty {
        display: none !important;
        height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* Plant name with animated gradient */
    .plant-name {
        font-size: 2.5rem;
        font-weight: 900;
        background: linear-gradient(135deg, #059669, #10b981, #34d399);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
        margin-bottom: 1.8rem;
        padding-bottom: 1.2rem;
        border-bottom: 3px solid #d1fae5;
        letter-spacing: -0.5px;
    }
    
    /* Status badges - enhanced with animations */
    .status {
        display: inline-block;
        padding: 0.75rem 2rem;
        border-radius: 50px;
        font-weight: 700;
        font-size: 1.1rem;
        margin: 0.5rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.12);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .status::before {
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        width: 0;
        height: 0;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.3);
        transform: translate(-50%, -50%);
        transition: width 0.6s, height 0.6s;
    }
    
    .status:hover::before {
        width: 300px;
        height: 300px;
    }
    
    .status:hover {
        transform: translateY(-3px) scale(1.05);
        box-shadow: 0 8px 20px rgba(0,0,0,0.18);
    }
    
    .status.healthy {
        background: linear-gradient(135deg, #10b981, #34d399);
        color: white;
    }
    
    .status.sick {
        background: linear-gradient(135deg, #ef4444, #f87171);
        color: white;
    }
    
    .status.info {
        background: linear-gradient(135deg, #3b82f6, #60a5fa);
        color: white;
    }
    
    /* Section headers - sleek modern style */
    .section-header {
        font-size: 1.5rem;
        font-weight: 800;
        color: #047857;
        margin: 2.5rem 0 1.2rem 0 !important;
        padding: 1rem 1.5rem;
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(5, 150, 105, 0.05));
        border-radius: 16px;
        border-left: 5px solid #10b981;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        transition: all 0.3s ease;
    }
    
    .section-header:hover {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(5, 150, 105, 0.08));
        transform: translateX(4px);
    }
    
    /* Force no white space between sections */
    .section-header + div,
    .section-header + .simple-list,
    .section-header + .info-box {
        margin-top: 0.5rem !important;
    }
    
    /* Info box - enhanced glassmorphism */
    .info-box {
        background: rgba(240, 253, 244, 0.9);
        backdrop-filter: blur(8px);
        border-left: 5px solid #10b981;
        padding: 1.8rem;
        margin: 1.2rem 0;
        border-radius: 16px;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.08);
        transition: all 0.3s ease;
    }
    
    .info-box:hover {
        box-shadow: 0 6px 16px rgba(16, 185, 129, 0.12);
        transform: translateX(2px);
    }
    
    .info-box p {
        margin: 0.6rem 0;
        color: #1f2937;
        line-height: 1.8;
        font-size: 1.05rem;
    }
    
    .info-box strong {
        color: #047857;
        font-weight: 700;
    }
    
    /* Simple list - modern card design */
    .simple-list {
        background: rgba(249, 250, 251, 0.95);
        backdrop-filter: blur(8px);
        padding: 1.8rem;
        border-radius: 16px;
        margin: 1.2rem 0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.06);
        border: 1px solid rgba(16, 185, 129, 0.1);
        transition: all 0.3s ease;
    }
    
    .simple-list:hover {
        box-shadow: 0 6px 16px rgba(0,0,0,0.08);
    }
    
    .simple-list ul {
        margin: 0;
        padding-left: 1.5rem;
    }
    
    .simple-list li {
        margin: 1.2rem 0;
        color: #1f2937;
        line-height: 1.8;
        font-size: 1.05rem;
        position: relative;
        padding-left: 0.5rem;
    }
    
    .simple-list li::marker {
        color: #10b981;
        font-weight: bold;
    }
    
    .simple-list li strong {
        color: #047857;
        font-weight: 700;
    }
    
    /* Button style - premium 3D effect */
    .stButton > button {
        background: linear-gradient(135deg, #10b981, #059669) !important;
        color: white !important;
        font-size: 1.25rem !important;
        padding: 1rem 3rem !important;
        border-radius: 16px !important;
        border: none !important;
        font-weight: 800 !important;
        box-shadow: 0 8px 20px rgba(16, 185, 129, 0.3), 
                    0 2px 4px rgba(0, 0, 0, 0.1) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        position: relative !important;
        overflow: hidden !important;
        letter-spacing: 0.5px !important;
    }
    
    .stButton > button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
        transition: left 0.5s;
    }
    
    .stButton > button:hover::before {
        left: 100%;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #059669, #047857) !important;
        box-shadow: 0 12px 28px rgba(16, 185, 129, 0.4), 
                    0 4px 8px rgba(0, 0, 0, 0.15) !important;
        transform: translateY(-3px) scale(1.02);
    }
    
    .stButton > button:active {
        transform: translateY(-1px) scale(0.98);
    }
    
    /* Radio buttons - modern card style */
    .stRadio > div {
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(8px);
        padding: 1.5rem;
        border-radius: 16px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.06);
        border: 1px solid rgba(16, 185, 129, 0.1);
        transition: all 0.3s ease;
    }
    
    .stRadio > div:hover {
        box-shadow: 0 6px 16px rgba(16, 185, 129, 0.12);
        border-color: rgba(16, 185, 129, 0.3);
    }
    
    .stRadio label {
        font-size: 1.08rem;
        font-weight: 600;
        color: #1f2937;
        transition: color 0.2s;
    }
    
    .stRadio label:hover {
        color: #047857;
    }
    
    /* File uploader styling - modern dashed border with animation */
    [data-testid="stFileUploader"] {
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(8px);
        padding: 2rem;
        border-radius: 20px;
        border: 3px dashed #10b981;
        transition: all 0.3s ease;
    }
    
    [data-testid="stFileUploader"]:hover {
        border-color: #059669;
        background: rgba(240, 253, 244, 0.95);
        transform: scale(1.01);
    }
    
    /* Success message */
    .stSuccess {
        background: #d1fae5;
        color: #065f46;
        border-radius: 12px;
        padding: 1rem;
        font-weight: 600;
    }
    
    /* Warning styling */
    .stWarning {
        border-radius: 12px;
    }
    
    /* Image container with hover effect */
    [data-testid="stImage"] {
        border-radius: 20px;
        overflow: hidden;
        box-shadow: 0 8px 20px rgba(0,0,0,0.12);
        transition: all 0.3s ease;
    }
    
    [data-testid="stImage"]:hover {
        box-shadow: 0 12px 32px rgba(0,0,0,0.16);
        transform: scale(1.02);
    }
    
    /* Footer tips - premium card design */
    .tips-footer {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        padding: 2.5rem;
        border-radius: 24px;
        margin-top: 3rem;
        box-shadow: 0 12px 32px rgba(0,0,0,0.1);
        text-align: center;
        border: 1px solid rgba(255, 255, 255, 0.5);
        transition: all 0.3s ease;
    }
    
    .tips-footer:hover {
        box-shadow: 0 16px 40px rgba(16, 185, 129, 0.15);
        transform: translateY(-2px);
    }
    
    .tips-footer strong {
        color: #047857;
        font-size: 1.3rem;
        font-weight: 800;
    }
    
    .tips-footer p {
        color: #4b5563;
        margin: 0.8rem 0;
        font-size: 1.05rem;
        font-weight: 500;
        transition: color 0.2s;
    }
    
    .tips-footer p:hover {
        color: #047857;
    }
    
    /* Divider - elegant gradient */
    hr {
        border: none;
        height: 3px;
        background: linear-gradient(to right, 
            transparent, 
            rgba(16, 185, 129, 0.3), 
            rgba(16, 185, 129, 0.6), 
            rgba(16, 185, 129, 0.3), 
            transparent);
        margin: 3rem 0;
        border-radius: 2px;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
    <div class="main-header">
        <h1>🌱 Plant Doctor</h1>
        <p>AI-Powered Plant Health Analysis • Get Instant Care Recommendations</p>
    </div>
""", unsafe_allow_html=True)

# API configuration
api_url = "http://localhost:8000"
fallback_url = "http://leaf-diseases-detect.vercel.app"


def display_complete_diagnosis(result):
    """Display full diagnosis from /diagnose endpoint"""
    
    # Plant name
    plant_name = result.get('plant_name', 'Your Plant')
    
    # Create main result container with plant name inside
    st.markdown(f'''
        <div class="result-box">
            <div class="plant-name">🌿 {plant_name}</div>
    ''', unsafe_allow_html=True)
    
    # Check if pipeline was successful
    if not result.get('pipeline_success', False):
        st.markdown("""
            <div class="info-box" style="background: linear-gradient(135deg, #fef3c7, #fde68a); border-left-color: #f59e0b;">
                <p>⚠️ Analysis completed with limited information</p>
            </div>
        """, unsafe_allow_html=True)
    
    # Health status
    health_status = result.get('health_status', 'unknown')
    
    if health_status == 'healthy':
        st.markdown('<div style="text-align: center;"><span class="status healthy">✅ Healthy Plant</span></div>', unsafe_allow_html=True)
        st.markdown('<div class="info-box"><p>🎉 Excellent! Your plant is in great health. Continue with your current care routine!</p></div>', unsafe_allow_html=True)
    
    elif health_status == 'unhealthy':
        st.markdown('<div style="text-align: center;"><span class="status sick">⚠️ Needs Attention</span></div>', unsafe_allow_html=True)
        
        # Disease info
        disease_info = result.get('disease_info', {})
        if disease_info.get('disease_detected'):
            disease_name = disease_info.get('disease_name', 'Unknown issue')
            severity = disease_info.get('severity', 'Unknown')
            
            st.markdown(f'<div class="info-box"><p><strong>What we found:</strong> {disease_name}</p><p><strong>How serious it looks:</strong> {severity}</p></div>', unsafe_allow_html=True)
            
            # Symptoms
            symptoms = disease_info.get('symptoms', [])
            if symptoms:
                symptoms_html = '<div class="section-header">🔎 What we observed</div><div class="simple-list"><ul>'
                for symptom in symptoms[:4]:
                    symptoms_html += f'<li>{symptom}</li>'
                symptoms_html += '</ul></div>'
                st.markdown(symptoms_html, unsafe_allow_html=True)
    
    else:
        st.markdown('<div style="text-align: center;"><span class="status info">ℹ️ Analysis Complete</span></div>', unsafe_allow_html=True)
    
    # Confidence score with detailed breakdown
    confidence = result.get('confidence', {})
    overall_conf = confidence.get('overall', 0)
    classification_conf = confidence.get('classification', 0)
    disease_conf = confidence.get('disease_detection', 0)
    calculation_method = confidence.get('calculation_method', 'adaptive_weighted')
    
    if overall_conf > 0:
        # Convert to percentage (0-1 to 0-100)
        overall_percent = overall_conf * 100 if overall_conf <= 1.0 else overall_conf
        classification_percent = classification_conf * 100 if classification_conf <= 1.0 else classification_conf
        disease_percent = disease_conf * 100 if disease_conf <= 1.0 else disease_conf
        
        # Display overall confidence in plain language
        st.markdown(
            f'<div style="text-align: center; margin: 1.5rem 0;">'
            f'<span class="status info">🎯 Overall confidence: {overall_percent:.1f}%</span>'
            f'<br><small style="color: #6b7280; font-size: 0.9rem;">How we estimated this: {calculation_method.replace("_", " ").title()}</small>'
            f'</div>', 
            unsafe_allow_html=True
        )
        
        # Show detailed confidence breakdown
        conf_breakdown = '<div class="section-header">📊 How confident we are</div><div class="info-box">'
        if classification_conf > 0:
            conf_breakdown += f'<p><strong>🌿 Plant Classification:</strong> {classification_percent:.1f}%</p>'
        if disease_conf > 0:
            conf_breakdown += f'<p><strong>🦠 Disease Detection:</strong> {disease_percent:.1f}%</p>'
        # Check both possible locations for KB confidence
        kb_conf = confidence.get('kb_confidence', 0) or result.get('kb_advice', {}).get('kb_confidence', 0)
        if kb_conf > 0:
            kb_percent = kb_conf * 100 if kb_conf <= 1.0 else kb_conf
            conf_breakdown += f'<p><strong>📚 Knowledge Base Match:</strong> {kb_percent:.1f}%</p>'
        conf_breakdown += '</div>'
        st.markdown(conf_breakdown, unsafe_allow_html=True)
    
    # Treatment recommendations
    # Build a focused treatment plan by merging LLM recommendations, model treatments, and KB guidance
    treatments = result.get('treatments', {})
    combined_treatments = treatments.get('combined_treatments', []) if isinstance(treatments, dict) else []
    llm_advice = result.get('llm_advice', {}) or {}
    llm_treatment = llm_advice.get('treatment_plan') or llm_advice.get('treatments') or []
    kb_advice = result.get('kb_advice', {}) or {}
    kb_treatments = kb_advice.get('treatments') or kb_advice.get('treatment_recommendations') or []

    # Observed symptoms (merge sources and show clearly)
    observed = []
    # disease_info symptoms (most direct)
    disease_info = result.get('disease_info', {}) or {}
    observed += disease_info.get('symptoms', []) if isinstance(disease_info.get('symptoms', []), list) else []
    # LLM reported symptoms
    observed += llm_advice.get('symptoms', []) if isinstance(llm_advice.get('symptoms', []), list) else []
    # KB reported symptoms
    observed += kb_advice.get('observed_symptoms', []) if isinstance(kb_advice.get('observed_symptoms', []), list) else []

    # Deduplicate while preserving order
    seen = set()
    observed_clean = []
    for s in observed:
        s_str = str(s).strip()
        if not s_str:
            continue
        if s_str.lower() in seen:
            continue
        seen.add(s_str.lower())
        observed_clean.append(s_str)

    if observed_clean:
        symptoms_html = '<div class="section-header">🔎 What we observed</div><div class="simple-list"><ul>'
        for sym in observed_clean[:8]:
            symptoms_html += f'<li>{sym}</li>'
        symptoms_html += '</ul></div>'
        st.markdown(symptoms_html, unsafe_allow_html=True)

    # Merge treatment sources into a single prioritized list
    merged = []
    for seq, src in ((llm_treatment, 'LLM'), (combined_treatments, 'Model'), (kb_treatments, 'KB')):
        if not seq:
            continue
        for step in seq:
            if not step:
                continue
            merged.append((str(step).strip(), src))

    # Also accept treatments provided directly under result keys
    if isinstance(result.get('treatment'), list):
        for t in result.get('treatment', []):
            merged.append((str(t).strip(), 'Model'))

    # Deduplicate keeping source priority (LLM -> Model -> KB)
    seen = set()
    focused_steps = []
    for text, src in merged:
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        focused_steps.append((text, src))

    # Prioritize urgent/containment actions first
    urgent_keywords = ('remove', 'isolate', 'prune', 'dispose', 'quarantine', 'spray', 'apply', 'sterilize', 'avoid', 'stop')
    urgent = [s for s in focused_steps if any(k in s[0].lower() for k in urgent_keywords)]
    non_urgent = [s for s in focused_steps if s not in urgent]
    ordered = urgent + non_urgent

    if ordered:
        # Filter out unhelpful steps before displaying
        filtered_steps = []
        for step, src in ordered[:8]:
            step_lower = step.lower()
            # Skip steps that indicate no information available
            if any(phrase in step_lower for phrase in [
                'no specific treatment',
                'not available',
                'information not found',
                'no information available',
                'unable to find'
            ]):
                continue
            filtered_steps.append((step, src))
        
        if filtered_steps:
            st.markdown('<div class="section-header">🛠️ What to do now</div>', unsafe_allow_html=True)
            plan_html = '<div class="simple-list"><ul>'
            for i, (step, src) in enumerate(filtered_steps, 1):
                # For a simple user view, show clear numbered steps
                extra = ''
                if src == 'KB' and kb_advice.get('kb_confidence'):
                    kb_conf = kb_advice.get('kb_confidence')
                    kb_percent = kb_conf * 100 if kb_conf <= 1.0 else kb_conf
                    extra = f' <span style="color:#10b981; font-size:0.85rem;">✓ Verified</span>'
                plan_html += f'<li><strong>Step {i}:</strong> {step}{extra}</li>'
            plan_html += '</ul></div>'
            st.markdown(plan_html, unsafe_allow_html=True)
    
    # Merge prevention tips from KB and LLM
    prevention = []
    prevention += kb_advice.get('prevention_tips', []) if isinstance(kb_advice.get('prevention_tips', []), list) else []
    prevention += llm_advice.get('prevention_tips', []) if isinstance(llm_advice.get('prevention_tips', []), list) else []
    prevention += result.get('prevention', []) if isinstance(result.get('prevention', []), list) else []

    # Deduplicate prevention tips
    seen = set()
    prevention_clean = []
    for tip in prevention:
        t = str(tip).strip()
        if not t:
            continue
        if t.lower() in seen:
            continue
        seen.add(t.lower())
        prevention_clean.append(t)

    if prevention_clean:
        prevention_html = '<div class="section-header">🛡️ Prevention Tips</div><div class="simple-list"><ul>'
        for tip in prevention_clean[:6]:
            prevention_html += f'<li>{tip}</li>'
        prevention_html += '</ul></div>'
        st.markdown(prevention_html, unsafe_allow_html=True)
    
    # Timestamp
    timestamp = result.get('timestamp', '')
    if timestamp:
        st.markdown(f'<div style="text-align: center; color: #9ca3af; font-size: 0.9rem; margin-top: 2rem;">📅 Analysis completed: {timestamp}</div>', unsafe_allow_html=True)
    
    # Close result box
    st.markdown('</div>', unsafe_allow_html=True)


def display_disease_detection(result):
    """Display disease detection results"""
    
    # Create main result container
    st.markdown('<div class="result-box">', unsafe_allow_html=True)
    
    if result.get("disease_type") == "invalid_image":
        st.markdown("""
            <div class="info-box" style="background: linear-gradient(135deg, #fef2f2, #fee2e2); border-left-color: #dc2626;">
                <p><strong>⚠️ Invalid Image</strong></p>
                <p>Please upload a clear photo showing plant leaves or affected areas.</p>
            </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        return
    
    if result.get("disease_detected"):
        disease_name = result.get('disease_name', 'Unknown Disease')
        st.markdown(f'<div class="plant-name">🦠 {disease_name}</div>', unsafe_allow_html=True)
        st.markdown('<div style="text-align: center;"><span class="status sick">⚠️ Issue Detected</span></div>', unsafe_allow_html=True)
        
        # Symptoms
        symptoms = result.get("symptoms", [])
        if symptoms:
            symptoms_html = '<div class="section-header">🔎 What we saw</div><div class="simple-list"><ul>'
            for symptom in symptoms[:3]:
                symptoms_html += f'<li>{symptom}</li>'
            symptoms_html += '</ul></div>'
            st.markdown(symptoms_html, unsafe_allow_html=True)
        
        # Treatment
        treatments = result.get("treatment", [])
        if treatments:
            treatment_html = '<div class="section-header">🛠️ Recommended Steps</div><div class="simple-list"><ul>'
            for i, treatment in enumerate(treatments[:5], 1):
                treatment_html += f'<li><strong>Step {i}:</strong> {treatment}</li>'
            treatment_html += '</ul></div>'
            st.markdown(treatment_html, unsafe_allow_html=True)
    else:
        st.markdown('<div class="plant-name">🌿 Healthy Plant</div>', unsafe_allow_html=True)
        st.markdown('<div style="text-align: center;"><span class="status healthy">✅ No Issues Found</span></div>', unsafe_allow_html=True)
        st.markdown("""
            <div class="info-box">
                <p>🎉 Great news! Your plant appears healthy with no visible diseases detected.</p>
            </div>
        """, unsafe_allow_html=True)
    
    # Close result box
    st.markdown('</div>', unsafe_allow_html=True)


# Mode selection
st.markdown('<div class="mode-card">', unsafe_allow_html=True)
st.markdown("<h3>🔬 Select Analysis Mode</h3>", unsafe_allow_html=True)
mode = st.radio(
    "",
    ["🌱 Full Diagnosis (Plant ID + Health Check)", "🔍 Quick Scan (Disease Detection Only)"],
    label_visibility="collapsed"
)
st.markdown('</div>', unsafe_allow_html=True)

# Upload section
st.markdown('<div class="upload-section">', unsafe_allow_html=True)
st.markdown("<h3>📸 Upload Plant Photo</h3>", unsafe_allow_html=True)
st.markdown("*For best results, use natural lighting and ensure the plant is clearly visible*")

col1, col2 = st.columns([1, 1])

with col1:
    uploaded_file = st.file_uploader(
        "Choose image", 
        type=["jpg", "jpeg", "png"],
        label_visibility="collapsed"
    )
    
    if uploaded_file is not None:
        st.image(uploaded_file, caption="📷 Uploaded Image", use_container_width=True)

with col2:
    if uploaded_file is not None:
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Set button text and endpoint based on mode
        if "Full Diagnosis" in mode:
            button_text = "🌱 Analyze Plant"
            endpoint = "/diagnose"
            spinner_text = "🔬 Analyzing plant health..."
        else:
            button_text = "🔍 Scan for Diseases"
            endpoint = "/disease-detection-file"
            spinner_text = "🔬 Scanning for diseases..."
        
        if st.button(button_text, use_container_width=True):
            with st.spinner(spinner_text):
                success = False
                result = None
                
                # Try local API first, then fallback
                for url in [api_url, fallback_url]:
                    try:
                        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                        response = requests.post(f"{url}{endpoint}", files=files, timeout=30)
                        
                        if response.status_code == 200:
                            result = response.json()
                            success = True
                            if url == api_url:
                                st.markdown("""
                                    <div style="background: #d1fae5; color: #065f46; padding: 0.8rem; border-radius: 10px; margin-bottom: 1rem; font-weight: 600; text-align: center;">
                                        ✅ Connected to local server
                                    </div>
                                """, unsafe_allow_html=True)
                            else:
                                st.markdown("""
                                    <div style="background: #dbeafe; color: #1e40af; padding: 0.8rem; border-radius: 10px; margin-bottom: 1rem; font-weight: 600; text-align: center;">
                                        ☁️ Connected to cloud server
                                    </div>
                                """, unsafe_allow_html=True)
                            break
                            
                    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                        continue
                    except Exception:
                        continue
                
                # Display results ONLY if successful
                if success and result:
                    
                    st.markdown('</div>', unsafe_allow_html=True)  # Close upload section
                    
                    # Display results without extra wrapper
                    if "Full Diagnosis" in mode:
                        display_complete_diagnosis(result)
                    else:
                        display_disease_detection(result)
                else:
                    st.markdown("""
                        <div style="background: #fee2e2; color: #991b1b; padding: 1rem; border-radius: 10px; margin-top: 1rem; font-weight: 600; text-align: center;">
                            ❌ Unable to connect to server. Please ensure the API is running.
                        </div>
                    """, unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
            <div style="background: #dbeafe; color: #1e40af; padding: 1rem; border-radius: 10px; text-align: center; font-weight: 600;">
                👆 Upload an image to begin analysis
            </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# Only show upload section closing tag if file wasn't uploaded
if uploaded_file is None:
    pass  # Already closed above
elif uploaded_file is not None and not st.session_state.get('button_clicked'):
    st.markdown('</div>', unsafe_allow_html=True)

# Footer tips
st.markdown("---")
st.markdown("""
    <div class="tips-footer">
        <p><strong>💡 Pro Tips for Accurate Results</strong></p>
        <p>✓ Use natural daylight for photography</p>
        <p>✓ Keep the camera focused on affected areas</p>
        <p>✓ Include both healthy and affected parts when possible</p>
        <p>✓ Avoid shadows and overexposure</p>
    </div>
""", unsafe_allow_html=True)