import csv
from utils.opensearch import OpenSearchService
from utils.embedding import get_embedding_bedrock
import boto3

def get_topoics():
    topics = []
    with open('configuration/guidance.csv', newline='') as csvfile:
        for row in csv.reader(csvfile, skipinitialspace=True):
            code = row[0]
            section = row[1]

            topic = code if len(section) ==0 else code + ' ' + section
            topics.append(topic)
    return topics

def get_guidelines(topic):
    topic_guidance = ''
    topic_sample = ''
    with open('configuration/guidance.csv', newline='') as csvfile:
        for row in csv.reader(csvfile, skipinitialspace=True):
            code = row[0]
            section = row[1]
            guidance = row[2]
            sample = row[3]

            key = code if len(section) ==0 else code + ' ' + section
            print(key)
            if key == topic:
                topic_guidance = guidance
                topic_sample = sample
                break
    return guidance,sample

def get_previous_report(topic,index,top_k int:=3,embedding_model str: = 'cohere.embed-multilingual-v3'):
    opensearch_client = OpenSearchService()
    query_embedding = get_embedding_bedrock(embedding_model,topic)
    results = opensearch_client.vector_search(query_embedding,index_name=index,size=top_k)
    previous_report_str = '<reports>'
    for result in results:
        source = result['_source']
        content = source['text']
        metadata = source['metadata']
        previous_report_str += '<report><file>'+metadata['source']+'</file><page_num>' + str(metadata['page_num']) + '</page_num><content>' + content + '</content></report>'
    previous_report_str += '</reports>'
    return previous_report_str
    

def get_prompt_template(step,topic):

    prompt = ''
    with open('configuration/prompt.csv', newline='') as csvfile:
        for row in csv.reader(csvfile, skipinitialspace=True):
            _step = row[0]
            _topic = row[1]
            _prompt = row[2]

            if step == _step and topic.find(_topic) >= 0:
                prompt = _prompt
                break

    return prompt
