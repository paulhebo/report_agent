import streamlit as st
import json
import time
from prompts import *
from generate_esg_report import get_report_agent
from generate_esg_report_sagemaker import get_report_agent_sagemaker

default_input_data= """
| Energy | 2020 | 2021 | 2022 | 2023 |
|--------|------|------|------|------|
| Natural gas purchased (GWh) | 1,873 | 1,744 | 1,655 | 1,567 |
| Electricity used (GWh) | 1,102 | 1,008 | 970 | 958 |
| Purchased renewable electricity (GWh) | 487 | 631 | 697 | 782 |
| Purchased non-renewable electricity (GWh) | 605 | 372 | 263 | 163 |
| On-site renewably generated electricity (GWh) | 19 | 13 | 18 | 17 |
| Exported electricity (GWh) | 9 | 8 | 8 | 4 |
| Coal (GWh) | 0 | 0 | 0 | 0 |
| Other fossil fuels (GWh) | 49 | 58 | 81 | 60 |
| Renewable heat (GWh) | 9 | 8 | 13 | 12 |
| Purchased heating and cooling (GWh) | 52 | 52 | 41 | 39 |
| Total energy for operations (GWh) | 3,085 | 2,871 | 2,759 | 2,636 |
| % renewable electricity | 46% | 63% | 73% | 83% |

| Carbon: Scope 1 and 2 emissions | 2020 | 2021 | 2022 | 2023 |
|--------------------------------|------|------|------|------|
| On-site fuel use (thousands of tonnes CO₂e) | 355 | 333 | 320 | 301 |
| Sales force vehicles (thousands of tonnes CO₂e) | 60 | 52 | 51 | 46 |
| Propellant emissions during manufacture of inhalers (thousands of tonnes CO₂e) | 275 | 237 | 243 | 220 |
| On-site waste or wastewater treatment (thousands of tonnes CO₂e) | 0 | 0 | 0 | 0 |
| Refrigerant gas losses (thousands of tonnes CO₂e) | 20 | 11 | 13 | 13 |
| Total Scope 1 emissions (thousands of tonnes CO₂e) | 711 | 633 | 626 | 581 |
| Electricity (market-based emissions) (thousands of tonnes CO₂e) | 163 | 125 | 84 | 60 |
| Purchased heating and cooling (thousands of tonnes CO₂e) | 6 | 6 | 4 | 4 |
| Total Scope 2 market-based emissions (thousands of tonnes CO₂e) | 169 | 131 | 88 | 64 |
| Total Scope 2 location-based emissions (thousands of tonnes CO₂e) | 309 | 285 | 265 | 240 |
| Total Scope 1 and 2 market-based emissions (thousands of tonnes CO₂e) | 879 | 764 | 715 | 645 |
| Fermentation/biogenic releases (thousands of tonnes CO₂e) | 27 | 18 | 12 | 12 |

| Carbon: Scope 3 emissions | 2020 | 2021 | 2022 | 2023 |
|--------------------------|------|------|------|------|
| Purchased goods and services (thousands of tonnes CO₂e) | 3,267 | 2,725 | 2,485 | - |
| Capital goods (thousands of tonnes CO₂e) | 162 | 154 | 161 | - |
| Fuel and energy-related activities (thousands of tonnes CO₂e) | 89 | 84 | 145 | - |
| Transportation and distribution (upstream) (thousands of tonnes CO₂e) | 267 | 189 | 242 | - |
| Waste generated in operations (thousands of tonnes CO₂e) | 20 | 64 | 51 | - |
| Business travel (thousands of tonnes CO₂e) | 42 | 50 | 85 | - |
| Employee commuting (thousands of tonnes CO₂e) | 37 | 48 | 60 | - |
| Leased assets (upstream) (thousands of tonnes CO₂e) | 0 | 0 | 0 | - |
| Transportation and distribution (downstream) (thousands of tonnes CO₂e) | 135 | 99 | 130 | - |
| Processing of sold products (thousands of tonnes CO₂e) | 0 | 0 | 0 | - |
"""


st.set_page_config(layout="wide")

with st.sidebar:
    st.title('Generate ESG report using LLM')

    model = st.radio(
    "**Select a model for report generation and evaluation**",
    ['us.anthropic.claude-3-7-sonnet-20250219-v1:0','us.anthropic.claude-3-5-sonnet-20241022-v2:0','amazon.nova-pro-v1:0','amazon.nova-lite-v1:0','jumpstart-dft-hf-llm-qwen2-5-7b-ins-20250520-094421']
    )

    report_score = st.slider("Report confidence score(range from 0 to 5)", 0.0, 5.0, 3.5)

    guidance_file = st.file_uploader("Upload a guildence file", type='csv')
    if guidance_file is not None:
        file_bytes = guidance_file.read()
        save_path = "configuration/guidance.csv"
        with open(save_path, "wb") as f:
            f.write(file_bytes)
        st.success(f"Guildence file saved to: {save_path}")

    prompt_file = st.file_uploader("Upload a prompt file", type='csv')
    if prompt_file is not None:
        file_bytes = prompt_file.read()
        save_path = "configuration/prompt.csv"
        with open(save_path, "wb") as f:
            f.write(file_bytes)
        st.success(f"Prompt file saved to: {save_path}")

    all_topics = get_topoics()
    topics = st.multiselect(
            "***Select topics***",
            all_topics,
            default=[all_topics[6],all_topics[7]]
    )
    
    user_data_list = []
    for topic in topics:
        user_data = st.text_area('For topic:' + topic+' ,input your data',default_input_data,height=500)
        user_data_list.append(user_data)

    gen_prompt_template = get_prompt_template(step='gen_report',topic=topics[0])
    regen_prompt_template = get_prompt_template(step='regen_report',topic=topics[0])
    eva_prompt_template = get_prompt_template(step='eva_report',topic=topics[0])
    final_prompt_template = get_prompt_template(step='final_report',topic=topics[0])

    gen_prompt_template = st.text_area(
        "Report generation prompt template",
        gen_prompt_template,
        key='prompt_key',
        height=400
    )

    evaluate_prompt_template = st.text_area(
        "Report evaluation prompt template",
        eva_prompt_template,
        key='evaluate_prompt_key',
        height=400
    )

    regen_prompt_template = st.text_area(
        "Re generation prompt template",
        regen_prompt_template,
        key='enhance_prompt_key',
        height=400
    )

    final_prompt_template = st.text_area(
        "Final report generation prompt template",
        final_prompt_template,
        key='final_report_prompt_key',
        height=400
    )

if st.button("Generate ESG report"):
    
    if model.find('qwen') >=0:
        report_agent = get_report_agent_sagemaker(model,report_score)
    else:
        report_agent = get_report_agent(model,report_score)

    input_body = {
            "topics": topics,
            "user_datas": user_data_list
            #"user_datas": [user_data]*len(topics)
        }

    for step in report_agent.stream(input_body):
        if 'contruct_report_prompts' in step.keys():
            with st.container(height=500):
                st.subheader('Generate repot prompt')
                st.divider()
                for gen_prompt in step['contruct_report_prompts']['gen_prompts']:
                    st.markdown(gen_prompt)
                    st.divider()
        elif 'call_generate_topic_report_agent' in step.keys():
            with st.container(height=500):
                st.subheader('Topic repot')
                st.divider()
                for topic_report in step['call_generate_topic_report_agent']['topic_reports']:
                    st.markdown(topic_report['topic'])
                    st.markdown(topic_report['topic_report'])
                    st.divider()
            with st.container(height=500):
                st.subheader('Topic repot evaluate result')
                st.divider()
                for eva_result in step['call_generate_topic_report_agent']['eva_results']:
                    st.markdown(eva_result['topic'])
                    st.markdown(eva_result['eva_result'])
                    st.markdown('Evaluate score:' + str(eva_result['eva_score']))
                    st.divider()
        elif 'generate_final_report' in step.keys():
            with st.container(height=500):
                st.subheader('Final repot')
                st.divider()
                st.markdown(step['generate_final_report']['final_report'][0])
        else:
            st.markdown(step)


