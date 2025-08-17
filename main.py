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
    st.set_page_config(page_title="SecAware", page_icon=":lock:", layout="wide")
    st.header(":lock: SecAware")
    
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

        INSTRUCTION2_ENCRYPTED = b'gAAAAABooiforARhgXeLpBdFc7oQ47eBmEDnzXvK5jNOluJYeYksIMZj5WG9scIsB-GWl7k8HQmHpQ5nZ51onZxW4-FuzVThOffeGGapqyH_CyRldxuHLLEftXd4l9DA-N6dIYLIKroWorKDCmlM8SJuHYpKT8fdDRKBhSJh4jI7cKEGMsFJQatOp_8ARYN0L5v7LBmrn5hp9w5WNxWGvZKjgdq-sH9fTmiK8twTYEdbui2TxFiYCQUjArlOn2VHRuMblYq-ZoBuxcnc-JnHUPn1hmxJX9zdCVAn9raPan2J9cJ7-gs1bWpa-awH_pDylM2XVer2yn27Hxoh6BloW0xrIqPuZNFimJ07ajQiiQfMPL1V6pwPVtdWlJsltojhdHqOBttJuDG4A4fvndoxK_mXysx8cFYIzqVw40tNVGWSxfnNtCXBLTSzduSaQjbkymndCGl5Zqjox4salbLFOSyYngP-tnr-V10vSEztnXoXDLfIOfQ6yHqx5ri6mCwUtZCdyBrcxFpOluCAf88kc76bdu2fiwx6yUrpk2TfOSre_YzwzXezfGxzqA4vz-9A2j29Qd5OdRe0pSsamymkkbJkt6JL9fwa7hu73_2kS9iEvfztVPQZTV40WpFvxEF9giZ80rNGEnO3RPaA1T1PBvuEANEYDdPVcY1NVRiw2cwoOsM9Kt8alDBDoP6-Al3CKEEPOXOiHyfYrfTmQ-lBT_vPVKKVUQAdaQYLfodSlaCT9yHquOLPvUEtBy-IhV5WyPA2tKD1bz-CYmgGuo1wNTtJZS78TZ6BeMlPCWmwIwFEVSMmf1oOwbnu3R1bwV1hlIWV_CZQ_sy8qhgr6X3zUF4cO45foG4KHvHmjbrvMq0gI7GY_43yiGQMmPPzjLDKFk6r6CmIqNDpLrt61utjP6r6uMFazVn13KrWdKkNefPwrxanJwbXsTFSYorVLH-vZBIcemK3CPANXyxkc7j60mM7HLfnHtUHSesh9_EC9-_snSzaMo4sskpxovh0d5EZEMcsx6wDy6ezotQIP4PLEa52au5xErmJPxK-A9-xgojjHk6ecNOXfRZzcWV70prL5IZmlKRGSExq5p6-j3tWeIB-6hkG9lHKhj-U8lyE9TU3KD5z0iLIInuTeIWAfpTjSsSISbE20rIkrcr49ZI0Fw20K3lUOgydi3g6He2flpARdGKVKakf5xwd1yealicPYfU5f81EwO9AceVUErYlg6zMjdUBgTW4bEd4Yrc75hlfRtBNKpIrNtyDnojA2LoPtIg1DgV4vgNqh_uSL7iOCmccl3GPpOR77amPB5vu9mF8kMHR7kqI03bhJtQxhdje6aTC46vacWMy-4ah9my-F4vawv3Vrk3_-J9zmkQE_V07v1-lsqZSsQIVR68UbZ64Vt1fhtbl0ioFe1LmQHwtI-mwtr2Zug1btJcMcvb556SXlJxzuKEPc-7woksykFdOTN1nOXtNf7WRpiz7doIdJNztFJ8eLiXEt4G0iaMcoa5826kcVCS_SDoLCnWCedNgO6leREktClbIZXyJCwK1kW63brG9woPOo7xawvQEOSGixS2v-M65SAK9YOxWsuMx9Op6nDlyWcCPS_Ghy8uTA8BtwYtMMDdmcR4Hhl_CXhe3lKuFlilApjqaChRDVABvi_gkbMNWtI-iEVFdQVtlofsLgBNrUStg_-KG9KqGKZKCPcJgZYl8dQ1pN5hY1_yZ-acUY1bl3Mk_1LtyQT9Hth_dM5YnPe7ymgQr1V2Rr9NCT4h8LSfYj5MVUtQjhiPBMo8GEHMrWU-tj9EkG-MWa0RtYtFveyG6lcq0OIfRha5hx6B586kel1vTuemq6pxnQ7wqql8QPRT6PYOeXCWbcnDZipBnXvYRIWmuPliUjMH5FVlBc7n095A4HYXLU18ezhCJ8TH5t01lpluohZ1n5e1rpUaEbYdO-VgPT8RK3bWrMQ_e44UL4WwdyS8cfNVebpoeX-CcNNdYcBibiEdzMwAm3XsZLzuxOVGh2LcOXlNUGHqwDtFuC9JV07Ln0JTdiH0736xb7SKFHbDuCmGD_zVSJ4qmjQrvIM6Fbcu26CjJyah8DVY6lvyJD5BmH-PyLB9wKcbrWLdSm38NbtykP1OzYbbuJhbNp1QxpyW6FUeaOiRHVAhObf2c5Y0TKcGxP5wYIRO-f9pKDA6bqGjjvVMK4Ap-zPgq5wE06s-aLqWrOw-nAkfKOtS3TaOtpEpr0zj0bKLrp4tEPc8MFXFVPBlK7L_URxfXPCGRGSIa7tnOlV2B67TITc3hRqAWkIwGUC4qakpWnbGSAyIndhP1gIEB8I9Dje58uln_XsxnDa84FRUi847OK9Qkg9jnFcA1TfD2R0vNE5pKvWvioMdaGFUVlk2PzM9g-yyv6mlTbANuc2j7CiQUgB8eWK6yHR0z1vXcPTX4C_vQG2csZcK8HhmhbdkpjWpqDaDfuLat-p4zk_uu5rDLpPV9BV59HKfkJ-q1T62m_t_cC2eAiXvOpImNjE8BQbyXTCsC-9anM_3LqXbX4j9VEGTKPZMFMcnRVdn3Mn5hh8rFw-Q_BfWAG1dQXcTY39l1NWAsWZ3MUPZpy4jK7CWcmuxwAItO70GhzO58JjrM5IKPyUeqZY22RHMXTcs3n9Qtb-mcSqh53gOcnyLThy4o0Hrp-Elf6bZuGqLT2KyZ_2JFKP-UuNfVYUe7tMdRLmZfJG3yarVa7RGE0SLqk6db_ck1cCJ7_MxUDHlfXVMbQSjRMCy8E-Z5KR_gyJYtMP9VNJCY_pDNvV3GIZ6pq3e39359mWYc8hLode_KPxuJjHR1W-S4gOdK8vjRIHe83QkKRAVSbH_KtrHMIgzUaqpetVOEW8d4B9zp4PjQZW0q9nFXJCrkHDJeqSl-h7SVcRPE3saK8HilXCgxmicSbJwfkHjKE8wcX_lnXSvXjxTpxHZ1acW0e1Ur81MJIK_rOu5_944qKaVK56TgmmV7h1nWkNkhycTvSfLUKrMGc4VIX3YUJhFcA8GE--s6ywQmBpxS1KLgw1EaboRh6dvySeA8qRqi75hrR_vH4UqbkzT29RQrn76cj5mrAuhxiwHxJlYjQQrtZBpWRCNenYoAcEPfIn1y0gI3J7dyeQM6hJTZECklJHSlIUpxeHJ_NdX7VOaDfkJf3jJI1_eP2y35_s_OFMiLndydMga1h5sStBzTeC8dIsKQi2x7Ws0qhbVlHi0WBJ8r6G3WfkYaBlq4oMn8A-cf5ywh37jFucEZB5ZK2ISNCxUMQH2XKMBF0AFTuZoqbO9qO9_iViCdwYSlyRfKpi6fHLOJejvjBDAiMjMx_nTR0OtOhTuOhPOH79mpECMj_0CFc4tvuLOmP3n31TZQ1VM4NW78qi8vgb2nz8JDpAR8to4VhAGVstHVX9Wh7THDR1M0Lk1kAQLLkScc1uihEjS4oGGz4cse9B_4xVkzh4ZZ91g3PCR6B3qJaVE5-_rJcDviWBR65QE120UQ_wHLwIyIzMq0u14w1VQOT_icQiCCR0ObumolRedoe6tWLN7D6LRcRVzYgbuwD0aCJFMiRQ2vPVEXVboH36o14pObPP3N3CtgHvN_zLmVaPvhaWE7419RO1QUmo313DG5kbgvttzGgbfRJQXaZC3ApzJtUIscIn98MiaXpLVEZbiSXJdY9VQOSFyu10qVom-CDvuK5irkYKYMmdH3PX_ZAHrUJCC2TsVODjhqFoS9yR6XwSh2N6NcFRcIPCSmN7MLEJBfcpANac2zppgt2Kni2ZaE9AMT3y_SiLLl3idH5FhcgOGgMEMRpCBUMp1cy3lBRCykCM1JYb9m4Bu7ew2hLzr9x1H-9RKpxHDvRLbXV6_Qwe-BYFKOaOQ06oCMtO0j1LuqH6h624uAwgyaCB3eLkjj1VSceJyBcoGvMp0BjqweykbwV_Z990cxkHjkIuTJqEDZZh4hC8LHmvRaXQzC4JItAyArzHk-5ST8CgZARt4iFpcM7mfOhPWbbbCvf-7Y_y_AQ-UXy7g_jFWh46ZXbzEQ6YuAGn6VdgYSqmgDRN4sEb_I9LgCChJ9SaY3dySjs65Lv3J7jo3sYdT5GGoackjo3up0IReRrlSsnm1gCsT-pNA_H6Fw5QLvtu03B_6rwF1F4RxSWTG3A4yNVduQ_pSlRF9372hZoHlBPBpOmbBVeLs7B9u08eAPGtMqNSnYc95fq_UqTp3zw-IB5NaQ-HxY3UrjsM3Fcde-a8hRyeAPf3QOChSH2d1TuxXUoI32HtLbcKIHe_NtuskxQV0ys78HX32s-NRQNAfy9rvBT97ygRZRZIqhQlYlFPKKL-kmr7ZRBmzaJSDWMxE0M0uZIe5Sin1AOJcjYj31Vdlylubn8CK8jRhElG0w3La3x0oj4MH2slG4kUHSBbRDLcFcePDpyixj8GeIYBcG8pw9gRd3qIkOfRT4cGeaQuQrIxnD9lGdxZabacD1N76cH1-V__BtZtLxiofguN7M835E2tKXn_Lc7GKa103kqOkXyY9HQuQRkwW-QHczWTy4U7O6ATbODHsjCBDb5RzL-z28DgdCJojgoeO5NqPH04L4-xXe9ifiMr-ohtzxUg0QfTZxHJDPScRAed1_ORu--SYKOld8QU45SQrWmwxyUAI7vDB8ud3AXTy12HrnBkQUwdA8gkow2HYYLoUvuVQXR6VY7e-JHAyu_6ZERfuN3qKh7X981amch0yPM413wxU5J0hnn3SJ9y15sMVd4PGeCxev5gb1p5-PLseu-Bm6AI9WKMxXFKbYO1fF5jCXd3kqUlaTJ7wqYDCk'
        key = st.secrets['INSTRUCTION_KEY'].encode()
        f = Fernet(key)
        INSTRUCTION2 = f.decrypt(INSTRUCTION2_ENCRYPTED).decode()

        # Create new form to search aitam library vector store.    
        with st.form(key="qa_form", clear_on_submit=False, height=300):
            query = st.text_area("**Inform your travel, stay safe on the move:**", height="stretch")
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
                    instructions = INSTRUCTION2,
                    input = query,
                    model = model,
                    temperature = 1.0,
                    tools = [
                        {
                            "type": "web_search"
                        },
                        # {
                        #     "type": "file_search",
                        #     "vector_store_ids": [VECTOR_STORE_ID],
                        # }
                    ],
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
                retrieved_files = set([response2.url for response2 in annotations])
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

elif st.session_state.get('authentication_status') is False:
    st.error('Username/password is incorrect')

elif st.session_state.get('authentication_status') is None:
    st.warning('Please enter your username and password')
