import csv


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

def get_pre_report(topic):
    pass

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
