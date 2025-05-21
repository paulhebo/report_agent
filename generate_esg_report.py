import boto3
from langchain_aws import ChatBedrockConverse 
from langchain_aws import ChatBedrock
from prompts import *
from typing import Annotated, TypedDict
from langchain_core.pydantic_v1 import BaseModel,Field
from langgraph.graph import END, StateGraph, START
from typing_extensions import Literal
from langgraph.constants import Send
import operator

from typing_extensions import Literal
from langchain_core.messages import HumanMessage, SystemMessage

bedrock_client = boto3.client("bedrock-runtime", region_name="us-west-2")

class GenTopicReportState(TypedDict):
    topic:str
    user_data:str
    gen_prompt: str
    topic_report: str
    eva_result: str
    eva_score: float

class TopicReport(BaseModel):
    topic_report: str

class TopicEvaResult(BaseModel):
    eva_result: str
    eva_score: float
    

class Feedback(BaseModel):
    grade: float = Field(
        description="Decide whether the report is high quality or not. the grade range from 0 to 5",
    )
    feedback: str = Field(
        description="If the report is not good, provide feedback on how to improve it.",
    )

class State(TypedDict):
    topics: list[str]
    user_datas: list[str]
    gen_prompts: list[str]
    topic_reports: Annotated[list[dict], operator.add]
    eva_results: Annotated[list[dict], operator.add]
    final_report: str


class TopicReports(BaseModel):
    topic_reports: list[str]

class FinalReport(BaseModel):
    final_report: str


def get_report_agent(model_name,report_score=3.5):

    model = ChatBedrockConverse(
        model=model_name,
        temperature=0,
        max_tokens=None,
        client=bedrock_client,
    )

    def gen_topic_report(state: GenTopicReportState):
        regen_prompt = ''
        if state['topic_report'] == '' and state['eva_result'] == '':
            regen_prompt = state['gen_prompt']
        else:
            regen_prompt_template = get_prompt_template(step='regen_report',topic=state['topic'])
            regen_prompt = regen_prompt_template.format(topic_report=state['topic_report'],eva_result=state['eva_result'])
        response = model.with_structured_output(TopicReport).invoke(regen_prompt)
        print('gen report response:',response.topic_report)
        return {"topic_report": response.topic_report}

    def eva_topic_report(state: GenTopicReportState):
        eva_prompt_template = get_prompt_template(step='eva_report',topic=state['topic'])
        eva_prompt = eva_prompt_template.format(topic_report=state['topic_report'])
        response = model.with_structured_output(TopicEvaResult).invoke(eva_prompt)
        print('eva report response:',response)
        return {"eva_result": response.eva_result, "eva_score": response.eva_score}


    def route_gen_report(state: GenTopicReportState):
        if float(state["eva_score"]) >= report_score:
            return "Accepted"
        elif float(state["eva_score"]) < report_score:
            return "Rejected + Feedback"


    gen_topic_report_builder = StateGraph(GenTopicReportState)

    gen_topic_report_builder.add_node("gen_topic_report", gen_topic_report)
    gen_topic_report_builder.add_node("eva_topic_report", eva_topic_report)

    gen_topic_report_builder.add_edge(START, "gen_topic_report")
    gen_topic_report_builder.add_edge("gen_topic_report", "eva_topic_report")
    gen_topic_report_builder.add_conditional_edges(
        "eva_topic_report",
        route_gen_report,
        {
            "Accepted": END,
            "Rejected + Feedback": "gen_topic_report",
        },
    )

    gen_topic_report_agent = gen_topic_report_builder.compile()
        
    def contruct_report_prompts(state: State):
        prompts = []
        for i in range(len(state['topics'])):
            topic = state['topics'][i]
            # print('topic:',topic)
            user_data = state['user_datas'][i]
            # print('user_data:',user_data)
            guidelines,sample = get_guidelines(topic)
            pre_report = get_pre_report(topic)
            gen_report_prompt_template = get_prompt_template(step='gen_report',topic=topic)
            prompt = gen_report_prompt_template.format(topic=topic, guidelines=guidelines, sample=sample, user_data=user_data)
        
            prompts.append(prompt)
        # print('prompts:',prompts)
        return {'gen_prompts':prompts}

    def call_generate_topic_report_agent(state: GenTopicReportState):
        response = gen_topic_report_agent.invoke({"topic": state["topic"],"gen_prompt": state["gen_prompt"],"topic_report":"","eva_result":""})
        return {"topic_reports": [{"topic": state["topic"],"topic_report": response['topic_report']}],"eva_results":[{"topic": state["topic"], "eva_result": response['eva_result'], "eva_score": response['eva_score']}]}

    def generate_final_report(state: State):
        topic_reports = state["topic_reports"]
        report_data = ''
        for topic_report in topic_reports:
            report_data += ('<topic_report><topic>' + topic_report['topic'] + "</topic><topic_report_content>" + topic_report['topic_report'] + "</topic_report_content></topic_report>" )

        final_prompt_template = get_prompt_template(step='final_report',topic=state['topics'][0])
        final_prompt = final_prompt_template.format(report_data=report_data)
        response = model.with_structured_output(FinalReport).invoke(final_prompt)
        return {"final_report": [response.final_report]}

    def continue_to_gen_report(state: State):
        return [Send("call_generate_topic_report_agent", {"topic": topic,"user_data": user_data, "gen_prompt": prompt}) for (topic,user_data,prompt) in zip(state["topics"],state['user_datas'],state["gen_prompts"])]


    graph = StateGraph(State)

    graph.add_node("contruct_report_prompts", contruct_report_prompts)
    graph.add_node("call_generate_topic_report_agent", call_generate_topic_report_agent)
    graph.add_node("generate_final_report", generate_final_report)

    graph.add_edge(START, "contruct_report_prompts")
    graph.add_conditional_edges("contruct_report_prompts", continue_to_gen_report, ["call_generate_topic_report_agent"])
    graph.add_edge("call_generate_topic_report_agent", "generate_final_report")

    app = graph.compile()

    return app



