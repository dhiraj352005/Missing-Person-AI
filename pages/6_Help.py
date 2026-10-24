import streamlit as st
from pages.helper import ui_theme

st.set_page_config(page_title="Help & User Guide — Suraksha AI", page_icon="📖", layout="wide")

# Inject Light Dashboard Theme & Sidebar
ui_theme.inject_custom_theme()
ui_theme.render_sidebar_profile()

# Page Header
ui_theme.render_page_header(
    title="System Help & Operational Guide",
    subtitle="Step-by-step user manual, troubleshooting FAQs, security protocols, and engineering contact support.",
    icon="📖",
)

# ── 1. USER GUIDE ─────────────────────────────────────────────────────────────
st.markdown("## 📘 User Guide")
st.markdown(
    """
    <p style="color: #64748B; font-size: 0.95rem; margin-top: -6px; margin-bottom: 18px;">
        Follow these standardized operational workflows to record missing person cases, monitor leads, and conduct facial recognition queries.
    </p>
    """,
    unsafe_allow_html=True,
)

guide_col1, guide_col2 = st.columns(2)

with guide_col1:
    # A. Register a Missing Person
    st.markdown(
        """
        <div class="modern-card" style="height: 100%;">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 10px;">
                <span style="background-color: #EFF6FF; color: #2563EB; font-weight: 800; font-size: 1.1rem; width: 32px; height: 32px; border-radius: 8px; display: inline-flex; align-items: center; justify-content: center; border: 1px solid #DBEAFE;">
                    A
                </span>
                <h3 style="margin: 0; font-size: 1.1rem; color: #0F172A; font-weight: 700;">
                    Register a Missing Person
                </h3>
            </div>
            <ol style="color: #334155; font-size: 0.9rem; line-height: 1.7; padding-left: 20px; margin: 0;">
                <li>Navigate to <b>Register New Case</b> in the sidebar navigation.</li>
                <li>Enter the required missing-person details (Full Name, Age, Gender, City, and Last Seen Location).</li>
                <li>Upload a clear photograph containing a visible face. If multiple faces appear, select the target bounding box.</li>
                <li>Fill in the complainant details (Name, Contact Number, and Email).</li>
                <li>Review the submitted information thoroughly and click <b>Save Case</b>.</li>
                <li>Note the generated <b>Case ID</b> for future tracking and cross-referencing.</li>
            </ol>
        </div>
        """,
        unsafe_allow_html=True,
    )

with guide_col2:
    # B. View and Manage Cases
    st.markdown(
        """
        <div class="modern-card" style="height: 100%;">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 10px;">
                <span style="background-color: #EFF6FF; color: #2563EB; font-weight: 800; font-size: 1.1rem; width: 32px; height: 32px; border-radius: 8px; display: inline-flex; align-items: center; justify-content: center; border: 1px solid #DBEAFE;">
                    B
                </span>
                <h3 style="margin: 0; font-size: 1.1rem; color: #0F172A; font-weight: 700;">
                    View and Manage Cases
                </h3>
            </div>
            <ol style="color: #334155; font-size: 0.9rem; line-height: 1.7; padding-left: 20px; margin: 0;">
                <li>Open <b>Cases Submitted by Me</b> to review reports originated under your officer credentials.</li>
                <li>Open <b>All Cases</b> to browse department-wide cases accessible to your jurisdiction.</li>
                <li>Use search fields and dynamic filters (Case ID, Name, City, or Status) to locate records quickly.</li>
                <li>Check the live case status badge (<b>Open / Missing</b> or <b>Found</b>) and examine detailed dossiers.</li>
                <li>Download case information as a structured <b>CSV</b> file for offline analytics and reporting.</li>
            </ol>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.write("")

guide_col3, guide_col4 = st.columns(2)

with guide_col3:
    # C. Find Potential Matches
    st.markdown(
        """
        <div class="modern-card" style="height: 100%;">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 10px;">
                <span style="background-color: #EFF6FF; color: #2563EB; font-weight: 800; font-size: 1.1rem; width: 32px; height: 32px; border-radius: 8px; display: inline-flex; align-items: center; justify-content: center; border: 1px solid #DBEAFE;">
                    C
                </span>
                <h3 style="margin: 0; font-size: 1.1rem; color: #0F172A; font-weight: 700;">
                    Find Potential Matches
                </h3>
            </div>
            <ol style="color: #334155; font-size: 0.9rem; line-height: 1.7; padding-left: 20px; margin: 0;">
                <li>Navigate to <b>Match Cases</b> from the navigation sidebar.</li>
                <li>Follow the existing image-matching workflow by selecting a target case record or uploading a suspect photo.</li>
                <li>Review candidate photographs, similarity percentage scores, and Euclidean distance metrics.</li>
                <li><b>Important:</b> Treat AI-generated matches as <i>potential matches only</i>; mandatory human verification is required before confirming an identity.</li>
            </ol>
        </div>
        """,
        unsafe_allow_html=True,
    )

with guide_col4:
    # D. View Case Locations
    st.markdown(
        """
        <div class="modern-card" style="height: 100%;">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 10px;">
                <span style="background-color: #EFF6FF; color: #2563EB; font-weight: 800; font-size: 1.1rem; width: 32px; height: 32px; border-radius: 8px; display: inline-flex; align-items: center; justify-content: center; border: 1px solid #DBEAFE;">
                    D
                </span>
                <h3 style="margin: 0; font-size: 1.1rem; color: #0F172A; font-weight: 700;">
                    View Case Locations
                </h3>
            </div>
            <ol style="color: #334155; font-size: 0.9rem; line-height: 1.7; padding-left: 20px; margin: 0;">
                <li>Open the <b>Map</b> page in the sidebar.</li>
                <li>Explore available case and citizen sighting locations rendered on the interactive Mapbox India view.</li>
                <li>Hover over or click markers to inspect municipal case statistics, active missing tallies, and resolution percentages.</li>
                <li>Review the city breakdown summary table below the map for national regional analytics.</li>
            </ol>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.write("")

# ── 2. TROUBLESHOOTING & FAQS ─────────────────────────────────────────────────
st.markdown("## ❓ Troubleshooting & Frequently Asked Questions")
st.markdown(
    """
    <p style="color: #64748B; font-size: 0.95rem; margin-top: -6px; margin-bottom: 14px;">
        Quick answers and diagnostic steps for common issues encountered during case registration, photo ingestion, and search.
    </p>
    """,
    unsafe_allow_html=True,
)

with st.expander("📌 Why is my photo not accepted?", expanded=False):
    st.write(
        "Upload a supported image (JPG, JPEG, or PNG) with a clear, visible face. "
        "Ensure the file size is within acceptable limits and follow any validation messages displayed by the application."
    )

with st.expander("📌 Why is no face detected?", expanded=False):
    st.write(
        "Try a clearer, front-facing photograph with adequate lighting and minimal obstruction. "
        "Avoid heavy motion blur, dark shadows, extreme head tilt angles, or subjects wearing sunglasses and face masks."
    )

with st.expander("📌 Why can I not find my submitted case?", expanded=False):
    st.write(
        "Check **Cases Submitted by Me**, verify that your search filters and status criteria are set correctly, "
        "and ensure you are logged into the exact officer account that originated the record."
    )

with st.expander("📌 What if no potential match is found?", expanded=False):
    st.write(
        "The person may not be present in the registered database yet, or the uploaded photograph may not provide sufficient "
        "biometric resolution for matching. Re-attempt with alternative photographs from different angles or check back as new citizen sightings are submitted."
    )

with st.expander("📌 What should I do if an error occurs?", expanded=False):
    st.write(
        "Note the exact error message or screenshot displayed on screen, refresh the application session, "
        "and contact the support team listed in the support section below for assistance."
    )

st.write("")

# ── 3. PRIVACY AND SECURITY ───────────────────────────────────────────────────
st.markdown(
    """
    <div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; border-left: 4px solid #2563EB; border-radius: 12px; padding: 20px 24px; margin-bottom: 28px; box-shadow: 0 1px 3px rgba(15,23,42,0.04);">
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 10px;">
            <span style="font-size: 1.3rem;">🛡️</span>
            <h3 style="margin: 0; font-size: 1.15rem; color: #0F172A; font-weight: 700;">
                Privacy & Data Security Protocols
            </h3>
        </div>
        <ul style="color: #334155; font-size: 0.9rem; line-height: 1.7; padding-left: 20px; margin: 0;">
            <li><b>Confidentiality:</b> Keep your officer login credentials and session tokens strictly confidential.</li>
            <li><b>Authorized Use:</b> Access and utilize missing person records solely for official investigation and law enforcement purposes.</li>
            <li><b>Data Protection:</b> Do not distribute sensitive photographs, biometric vectors, or complainant contact numbers publicly.</li>
            <li><b>Verification Standard:</b> Remember that AI-generated facial scores are computational indicators and <i>not proof of legal identity</i>. Formal physical corroboration is mandatory.</li>
        </ul>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── 4. CONTACT SUPPORT ────────────────────────────────────────────────────────
st.markdown("## 📞 Need Help? Contact Our Team")
st.markdown(
    """
    <p style="color: #64748B; font-size: 0.95rem; margin-top: -6px; margin-bottom: 20px;">
        For technical issues, account assistance, or questions about using the system, contact our support team.
    </p>
    """,
    unsafe_allow_html=True,
)

contact_col1, contact_col2 = st.columns(2)

with contact_col1:
    # Contact 1: Dhiraj
    st.markdown(
        """
        <div class="modern-card" style="padding: 16px 20px; margin-bottom: 14px; border-left: 3px solid #2563EB;">
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <div>
                    <div style="font-weight: 700; color: #0F172A; font-size: 1.05rem;">
                        Dhiraj
                    </div>
                    <div style="font-size: 0.8rem; color: #64748B; margin-top: 2px;">
                        Engineering & System Architecture
                    </div>
                </div>
                <span style="background-color: #EFF6FF; color: #2563EB; width: 38px; height: 38px; border-radius: 8px; display: inline-flex; align-items: center; justify-content: center; font-size: 1.2rem; border: 1px solid #DBEAFE;">
                    ✉️
                </span>
            </div>
            <div style="margin-top: 12px; padding-top: 10px; border-top: 1px solid #F1F5F9;">
                <a href="mailto:dhiraj352005@gmail.com" style="color: #2563EB; font-weight: 600; text-decoration: none; font-size: 0.9rem; display: inline-flex; align-items: center; gap: 6px;">
                    <span>dhiraj352005@gmail.com</span>
                    <span style="font-size: 0.75rem;">↗</span>
                </a>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Contact 3: Abhishek
    st.markdown(
        """
        <div class="modern-card" style="padding: 16px 20px; margin-bottom: 14px; border-left: 3px solid #2563EB;">
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <div>
                    <div style="font-weight: 700; color: #0F172A; font-size: 1.05rem;">
                        Abhishek
                    </div>
                    <div style="font-size: 0.8rem; color: #64748B; margin-top: 2px;">
                        Computer Vision & Facial Recognition Pipeline
                    </div>
                </div>
                <span style="background-color: #EFF6FF; color: #2563EB; width: 38px; height: 38px; border-radius: 8px; display: inline-flex; align-items: center; justify-content: center; font-size: 1.2rem; border: 1px solid #DBEAFE;">
                    ✉️
                </span>
            </div>
            <div style="margin-top: 12px; padding-top: 10px; border-top: 1px solid #F1F5F9;">
                <a href="mailto:abhishek.raj23@pccoepune.org" style="color: #2563EB; font-weight: 600; text-decoration: none; font-size: 0.9rem; display: inline-flex; align-items: center; gap: 6px;">
                    <span>abhishek.raj23@pccoepune.org</span>
                    <span style="font-size: 0.75rem;">↗</span>
                </a>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with contact_col2:
    # Contact 2: Sachin
    st.markdown(
        """
        <div class="modern-card" style="padding: 16px 20px; margin-bottom: 14px; border-left: 3px solid #2563EB;">
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <div>
                    <div style="font-weight: 700; color: #0F172A; font-size: 1.05rem;">
                        Sachin
                    </div>
                    <div style="font-size: 0.8rem; color: #64748B; margin-top: 2px;">
                        Backend Operations & Cloud Database
                    </div>
                </div>
                <span style="background-color: #EFF6FF; color: #2563EB; width: 38px; height: 38px; border-radius: 8px; display: inline-flex; align-items: center; justify-content: center; font-size: 1.2rem; border: 1px solid #DBEAFE;">
                    ✉️
                </span>
            </div>
            <div style="margin-top: 12px; padding-top: 10px; border-top: 1px solid #F1F5F9;">
                <a href="mailto:sachin2803@gmail.com" style="color: #2563EB; font-weight: 600; text-decoration: none; font-size: 0.9rem; display: inline-flex; align-items: center; gap: 6px;">
                    <span>sachin2803@gmail.com</span>
                    <span style="font-size: 0.75rem;">↗</span>
                </a>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Contact 4: Vaibhav
    st.markdown(
        """
        <div class="modern-card" style="padding: 16px 20px; margin-bottom: 14px; border-left: 3px solid #2563EB;">
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <div>
                    <div style="font-weight: 700; color: #0F172A; font-size: 1.05rem;">
                        Vaibhav
                    </div>
                    <div style="font-size: 0.8rem; color: #64748B; margin-top: 2px;">
                        Security Architecture & Authentication
                    </div>
                </div>
                <span style="background-color: #EFF6FF; color: #2563EB; width: 38px; height: 38px; border-radius: 8px; display: inline-flex; align-items: center; justify-content: center; font-size: 1.2rem; border: 1px solid #DBEAFE;">
                    ✉️
                </span>
            </div>
            <div style="margin-top: 12px; padding-top: 10px; border-top: 1px solid #F1F5F9;">
                <a href="mailto:vaibhav.hatwate23@pccoepune.org" style="color: #2563EB; font-weight: 600; text-decoration: none; font-size: 0.9rem; display: inline-flex; align-items: center; gap: 6px;">
                    <span>vaibhav.hatwate23@pccoepune.org</span>
                    <span style="font-size: 0.75rem;">↗</span>
                </a>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
