import streamlit as st
from case_analysis import case_analysis_app
from document_verification import document_verification_app

def main():
    st.set_page_config(page_title="RERA Project", page_icon='⚖️')
    if "page" not in st.session_state:
        st.session_state.page = "home"

    if st.session_state.page == "home":
        show_home()
    elif st.session_state.page == "case_analysis":
        case_analysis_app()
    elif st.session_state.page == "document_verification":
        document_verification_app()

def show_home():
    st.title("Legal Compliance & Case Analysis")
    st.write("Choose a feature:")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Case Analysis", use_container_width=True):
            st.session_state.page = "case_analysis"
            st.rerun()
    with col2:
        if st.button("Document Verification", use_container_width=True):
            st.session_state.page = "document_verification"
            st.rerun()

if __name__ == "__main__":
    main()
