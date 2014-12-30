# python program designed to simulate a baseball game

import boto.sqs
conn = boto.sqs.connect_to_region("us-west-2")

# use time for sleeper and random to generate numbers to help simulate outcome

import time
import random
import json

# connect to the AtBat SQS queue

my_queue = conn.get_queue('AtBat')
print 'queue name'
print my_queue

from boto.sqs.message import Message

# write messages out to the queue that randomly generate at bats

for i in range(1, 1001):
    m = Message()

    outcome = random.randrange(1, 600)

    if outcome < 25:
        atbat = 'homerun'
    elif outcome < 32:
        atbat = 'triple'
    elif outcome < 70:
        atbat = 'double'
    elif outcome < 175:
        atbat = 'single'
    elif outcome < 300:
        atbat = 'groundout'
    elif outcome < 400:
        atbat = 'strikeout'
    else:
        atbat = 'flyout'

    y = '{"atbat" : "' + atbat + '", "random" : ' + str(outcome) + '}'
    x = json.loads(y)

    m.set_body(y)
    m.message_attributes = {"Label":{"data_type": "String", "string_value": "Baseball"},
                            "Sequence":{"data_type": "Number", "string_value": i }}
    my_queue.write(m)

    print m.get_body()

    time.sleep(.01)

print 'generation complete'



