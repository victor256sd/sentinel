import streamlit as st
import streamlit_authenticator as stauth
import openai
from openai import OpenAI
import os
import time
import yaml
from yaml.loader import SafeLoader
from pathlib import Path
from cryptography.fernet import Fernet
import re

# Disable the button called via on_click attribute.
def disable_button():
    st.session_state.disabled = True        

# Definitive CSS selectors for Streamlit 1.45.1+
st.markdown("""
<style>
    div[data-testid="stToolbar"] {
        display: none !important;
    }
    div[data-testid="stDecoration"] {
        display: none !important;
    }
    div[data-testid="stStatusWidget"] {
        visibility: hidden !important;
    }
</style>
""", unsafe_allow_html=True)

# Load config file with user credentials.
with open("config.yaml") as file:
    config = yaml.load(file, Loader=SafeLoader)

# Initiate authentication.
authenticator = stauth.Authenticate(
    config['credentials'],
)

# Call user login form.
result_auth = authenticator.login("main")
    
# If login successful, continue to aitam page.
if st.session_state.get('authentication_status'):
    authenticator.logout('Logout', 'main')
    st.write(f'Welcome *{st.session_state.get('name')}* !')

    # # Initialize chat history.
    # if "ai_response" not in st.session_state:
    #     st.session_state.ai_response = []
    
    # Model list, Vector store ID, assistant IDs (one for initial upload eval, 
    # the second for follow-up user questions).
    MODEL_LIST = ["gpt-4o-mini"] #, "gpt-4.1-nano", "gpt-4.1", "o4-mini"]
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
    VECTOR_STORE_ID = st.secrets["VECTOR_STORE_ID"]
    INSTRUCTION_ENCRYPTED = b'gAAAAABoogjtpudy9j4OOEWmJm2_OnObp0wmq_EVIVcEO_Dn0cGpZajivQPAvIYLaFl9_YkfbPoHxUdeqHAv0HzNNGZvrE7q5WlXZSVnUGRjpr1JtNs07MakJrHXQMSOkfFturCmIme5EmC1rwd5GyiVOcysugoMt1LHCDAVWjjAf3h0mZMP4bl5bzToUFGEVboD0GF8V84JlBEDTXFVBWr4oaf9qZBjf3UlzYw_2ZutiQsWmjsIOz7cydBnAomHklNjQzjK-IYNUucD8IT0WdgjbV_V8alitHPUph20RrGD5mfflhcS1Zckn89WZ_OP3cu1qauZOD_v4UscYcwnUR_u9Vd7BcRt9MJ0laBcB6NxkKTWOTr3Nz-3bN3NrBNL5ZUZdzl228Gnn-YqWqxaj_pn0zvZqqh3HlnXD8pqp64T-zVhTLDUuabi2J0puUJJoCiqHRXEES-qvPmBgPCKE-2bZ4fIYlLGZgVunfNloyJ8g2ha1BGKA5jF-KeGaZBJ3oisRwWvf_Me-R0crL-YxqBh7lyc0R7NvmS6qqKfAxf_Vv1HESbClVy3nr8G2aIKHcs71e5E1WUf4JewQzg5W6VyBTiKnlpUduBIOrVbISGZoYkxzjrSSipszHOEdgHKZcwSotEFVARiiFd47_ZTtYT_mSafsuXn_mGqOdfdDOX3fKG1Wu3zLGQ6xK87c3lw9LexE9OM3IhM2glXexfZ18WSJsyc76dov4xzUkNKpUVUra8I-mOt-CilJNh6IcMbXKEK4rVuacY9ocBarsxbT-_Xa8Mh-t28-3DuhOVk35rnS0YPg31KxxHi_IQfvnGJp4mnwxpqhvIKgLCluP1czNbhvxgfKCK0PgSnlRm4u1A9dfdBsyWhqZpjKH8HcnvSZ5DvIjZmnP24-goXsEug9j8paHIIXrd560NKHxhx-P0DvFg5ue9G0ldC2jppZAqgv55proUn63x7-AXJWAlJ5oYtbdEYEpHVEKo7xiwMs5wK5S6Oib3rq4K3EbCqtT-nCXOF1ftMbbJGUKCJhJeqMS0PNd-BSuedZN-oCRB3iVT7aOBEtADhURhVTe8NzLk9m98kLN9ngfstTEoxNAomAAYBikjibcflVy4OVgaViMD23Kzd3RV4IL17II9quT9cHouEZXW7FJ0je09afxyaPHlo9uee5653rtJ8Z_5Jh0Ljhp-QOjaFLlXeaMDrHi5uXu7uKaNW9epUJ6DKiJ7BY54NR1svpoGAy4n4EwS89RsvHXNzZsWmhRSnLrpWBx3voLR3NCqIaPpv9l5G9HjIh4jXJj5cn55Dbxeg0mHstUpqSL8KBZn6AcuU1BR_rvV3_-c6CJd3KuhBj5HQmW7e7iTVYDuLoXKaNvCuHAzMOBPgAUnqOQDzpQ_8FuKWsSxTkq_CclkNqN4x0s3XMEZSnz48u3ntM2ix5r6ZmgEbuan0UA_rctxpPrwf30cr9RIcQHOJ8D5JhmXIk-J4jVaiwFEjaytzGKXndMHAxOGZGrFy9xQbjGJyQvFdO5zrLcS84fzf0NojBrNkDtMOKRs3U2-cFvUTkSBv7IwtIti6UnbDB0iPvEIWhY2Zu0390DlsXuxFLTTQVnW4Cjb4KOBOzHzMEQEg_gP2g70IFVi1wfWL6DF0E7Gy2A3LJvfbGzgAV3p5cxWSVhxbf3mKI5Jxb3q1f-0sScxGIBoCtxL3VI_Y7IZ_D3ft01YtnXr_TInoU4ArXji6uN5W22R_0FQET-oGBzXTNhmSRRsXP3obR7vU_vnc16ivTgUzbitVES4U0oGwVhdFM2OYU7A8d_-29q4WqiLpvK9xeaZYovAHUCaaaMrDznhkzPVrAXV7AA8Y9jGP244dv3RXYB1mPy14te6ZVqh6coiysfwxmfpMNE8zw0dUkDY1Lnj0MTkpJp0lltjIvSdwzNLT5l2flFTTm2FxsALCB7TpBgC9DBTPU73rvikEcgr0HH2bD5QrCmDgW3nf8VfteTY7QyVP9Ki_9G2t4ZrrbCmSlzOgT10q_KgZosF91oMF-_yLLiTlsmA8k_M00Ia7LWtSUIQt3Rnth3gWbskX5qz6ydwXKyzgsHuZRy4rXMOrRkgXwOHW7M4x7rlVWe-RTTSTAr1j2IvodbKytPOsWIeZLYp027rUOtMvCU-o2pD8D1ViRenlyQwVNcI7QS1_GLzPIYx-wASN19CyqVYtLSY7CK9DFBKi-N1YL7eHLmIuo2TiBLYDQ4JApenAIj6XLF3R5Af2Bg-G8fbeLp75rQyoJUgHckPK2ufpptL_vwip_C2obUwdC_j8OsUNkMiBXMXWYRsGKITPDBi4RdYOfRP3-SdXNqYoeN1PeOiLUTj2_xuVKyhTE_nJSQjKz_vEaEmmlmkj8WSPO_iGhwi82IyaselIraTsb4idHkIDXiScSZG8KVkuUmdCwTeriMYPHOlzxIi9hmPmyIn9Ipak6BaV3sTG3Yw89HBbtBEWGXOYJyVJlsnqfMAtoc3V1_FU4R4lNFVJigh7SJPJFMgA3NbG7pluYC5sEkXv5giWfIJTuh2J6s8JW0fOyeAI4vnNdh6bG2cyHYz_Ac3PWq__st_CAsQOKmS6ml3SREIY6KHqrsQC-2GkHuWCfPgVbLtDAf6VfMnc-qCge0Wy6PfeD4b__RJ9byH3vqQMoFwB-z5iOL_80Ho0EfruHBVNef8lFiTFRDsGYviyMLEteo4BJMMz3YIQRSFntj0pnaEwU7XkMS6yeGBwQkzjLkOKzwVnjEISmENHp6h1KBWHw87VoHsSrVR7pWYEEpT2VGTMNnvxayr8XD9CN1kar_W5uBTBKHhoMFTklb6KeQ-QucJa3GyBTN0yQREHvkytZTzLZbnzygaZpf1nvTav7tvsbOvVUIOs5l95enuQqtBn8mydpDsGL9NehFh0k1fLC7sIOSN6nA4Jo7aPIo1rflKBT670oOEVCwjONhEtLeXGFovkArxvNq9nER9YJ6S94kam44A-My2g8qV8H-MLPUduf0Ognm8unBqN0F4rcrkqOGSJ7nna2vWMXTXkC9X4c08oOtFxdhSBZnXfI_ohQGCEeMb6jdqkSPfFqHoFpjDlCwyfeX0fmMC1knsrEhm2t7q_qW4v0z-fUYBF1VVb8yw9B2p9pNgwSR7mo-5yiLBrtymazyrIyMe71pjbbIAsWVPI-5nrWIvj3NvKJx5ZYdncvaA2tjZ0xLy7u5SchpQOx8cE5jsEt5GHTK3TynvOfCNjo27LrQIVhyKedL5fLbf9yCTbekKUpXlWCG1HI6xRLUFIKOYnpa1H4nh5NvK7BapPZ11SFepqlvJnTCe1Q1uPwx8i-FUXRGnvYWDk-8Tx7bNy3imYxxu-D3LuM_G3BRODg7wUFjARHwb9ewlCLjpzGyeszWjKdNBNPV_Hjm-1Zi-kKQgO0i2HvKiDHS9vZn5TqrvyvIdi6VDwcC-J6edxGsR_l8tLATKS_1EyeYb7tec3OqA92m620mIknwPVYxSNVwweCxBpY9oHtykJuoZIFl9SfA1bKxOj6y7BlR3EswEzP5Quj6bOcCuBgXNs6OziO5I4Gklj2wXY9PMROX5jprYleq7RqYxv6oGSKi_ImUHN9z_QvHU5hcw37DQPQI9xWwYgkL_92YaspqGvvQO2df8lbpuxfBS5nMHp3NH9ZlZ43JiKoRanCyQgLrLQ9yPA4nRUzZbhdN-wstWaO0jfY3rmc1m7C3LZ2EN1xWPXNOHMPBI4fHrjngRHDTJt1vFI_acXxsvAREEWAjhlwjQAUCtRGY7hL4Ac2-ImXTtBgdyKzuPCwQMfZqt9k9ZDjg_wSOJfIbNLrXTOCP4V1A3maA-YB18Twv4AA-ey_su-NxBaX9WBTZibg175tAAmlwweirXDNs5AA7dJ7uZSniDjqE-q1Gy4jncmjd0ljkaXhv4yXNs_HA=='

    key = st.secrets['INSTRUCTION_KEY'].encode()
    f = Fernet(key)
    INSTRUCTION = f.decrypt(INSTRUCTION_ENCRYPTED).decode()

    # Set page layout and title.
    st.set_page_config(page_title="SecAware", page_icon=":rotating_light:", layout="wide")
    st.header(":rotating_light: SecAware")
    
    # Field for OpenAI API key.
    openai_api_key = os.environ.get("OPENAI_API_KEY", None)

    # Retrieve user-selected openai model.
    model: str = st.selectbox("Model", options=MODEL_LIST)

    selection = st.radio(
        "Sentinel AI Tools:",
        ["Advisor", "TripAdvance"],  
        captions=[
            "*Insights for corporate and personal protection*",
            "*Travel security recommendations*",
        ],
    )
    
    # If there's no openai api key, stop.
    if not openai_api_key:
        st.error("Please enter your OpenAI API key!")
        st.stop()

    if selection == "Advisor":
        # Create new form to search aitam library vector store.    
        with st.form(key="qa_form", clear_on_submit=False, height=300):
            query = st.text_area("**Ask security questions, get answers:**", height="stretch")
            submit = st.form_submit_button("Send")
            
        # If submit button is clicked, query the aitam library.            
        if submit:
            # If form is submitted without a query, stop.
            if not query:
                st.error("Enter a request!")
                st.stop()            
            # Setup output columns to display results.
            answer_col, sources_col = st.columns(2)
            # Create new client for this submission.
            client2 = OpenAI(api_key=openai_api_key)
            # Query the aitam library vector store and include internet
            # serach results.
            with st.spinner('Searching...'):
                response2 = client2.responses.create(
                    instructions = INSTRUCTION,
                    input = query,
                    model = model,
                    temperature = 0.6,
                    tools = [{
                                "type": "file_search",
                                "vector_store_ids": [VECTOR_STORE_ID],
                    }],
                    include=["output[*].file_search_call.search_results"]
                )
            # Write response to the answer column.    
            with answer_col:
                cleaned_response = re.sub(r'【.*?†.*?】', '', response2.output[1].content[0].text)
                st.markdown("#### Response")
                st.markdown(cleaned_response)
                # st.session_state.ai_response = cleaned_response
            # Write files used to generate the answer.
            with sources_col:
                st.markdown("#### Sources")
                # Extract annotations from the response, and print source files.
                annotations = response2.output[1].content[0].annotations
                retrieved_files = set([response2.filename for response2 in annotations])
                file_list_str = ", ".join(retrieved_files)
                st.markdown(f"**File(s):** {file_list_str}")
    
                st.markdown("#### Token Usage")
                input_tokens = response2.usage.input_tokens
                output_tokens = response2.usage.output_tokens
                total_tokens = input_tokens + output_tokens
                input_tokens_str = f"{input_tokens:,}"
                output_tokens_str = f"{output_tokens:,}"
                total_tokens_str = f"{total_tokens:,}"
    
                st.markdown(
                    f"""
                    <p style="margin-bottom:0;">Input Tokens: {input_tokens_str}</p>
                    <p style="margin-bottom:0;">Output Tokens: {output_tokens_str}</p>
                    """,
                    unsafe_allow_html=True
                )
                st.markdown(f"Total Tokens: {total_tokens_str}")
    
                if model == "gpt-4.1-nano":
                    input_token_cost = .1/1000000
                    output_token_cost = .4/1000000
                elif model == "gpt-4o-mini":
                    input_token_cost = .15/1000000
                    output_token_cost = .6/1000000
                elif model == "gpt-4.1":
                    input_token_cost = 2.00/1000000
                    output_token_cost = 8.00/1000000
                elif model == "o4-mini":
                    input_token_cost = 1.10/1000000
                    output_token_cost = 4.40/1000000
    
                cost = input_tokens*input_token_cost + output_tokens*output_token_cost
                formatted_cost = "${:,.4f}".format(cost)
                
                st.markdown(f"**Total Cost:** {formatted_cost}")

    elif selection == "TripAdvance":
        # Create new form to search aitam library vector store.    
        with st.form(key="qa_form", clear_on_submit=False, height=300):
            query = st.text_area("**Inform your travel, stay safe on the move:**", height="stretch")
            submit = st.form_submit_button("Send")

elif st.session_state.get('authentication_status') is False:
    st.error('Username/password is incorrect')

elif st.session_state.get('authentication_status') is None:
    st.warning('Please enter your username and password')
