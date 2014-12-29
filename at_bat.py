
# testing out SQS functionality

import boto.sqs
conn = boto.sqs.connect_to_region("us-west-2")

# use time for sleeper and random to generate numbers to help simulate outcome

import time
import random

# connect to the AtBat SQS queue

my_queue = conn.get_queue('AtBat')
print 'queue name'
print my_queue

from boto.sqs.message import Message

# write messages out to the queue that randomly generate at bats

for i in range(1, 1001):
    m = Message()

    outcome = random.randrange(1, 600)
    print outcome

    if outcome < 40:
        m.set_body('homerun')
    elif outcome < 50:
        m.set_body('triple')
    elif outcome < 90:
       m.set_body('double')
    elif outcome < 200:
        m.set_body('single')
    elif outcome < 300:
        m.set_body('groundout')
    elif outcome < 400:
        m.set_body('strikeout')
    else:
        m.set_body('flyout')

    m.message_attributes = {"Label":{"data_type": "String", "string_value": "Baseball"},
                            "Sequence":{"data_type": "Number", "string_value": i }}
    my_queue.write(m)
    print m.get_body()
    time.sleep(.1)


