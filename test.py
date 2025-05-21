import csv


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

topic = 'GRI 101-1'
topic_guidance,topic_sample = get_guidelines(topic)
print(topic_guidance)
print(topic_sample)
