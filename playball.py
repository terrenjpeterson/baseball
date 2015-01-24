# used to connect to SQS

import boto.sqs
conn = boto.sqs.connect_to_region("us-west-2")

import time
import json

# these are used to create API calls and write to a buffer

import pycurl
import cStringIO

# initialize global variables to begin the game

gamespeed = 0.1

out = 0
inning = 1

visitor_score = 0
home_score = 0

visitor_name = 'visiting team'
home_name = 'home team'

h_ab = [0] * 10
v_ab = [0] * 10

h_hit = [0] * 10
v_hit = [0] * 10

h_lineup = []
h_positions = []

v_lineup = []
v_positions = []

visitor_batter_up = 1
home_batter_up = 1

visitor_pitches_thrown = 0
home_pitches_thrown = 0

visitor_atbat = True
game_inprogress = True

runner_on_first = False
runner_on_second = False
runner_on_third = False

# connect to the Baseball Schedule queue to see if any games are to be played

my_queue = conn.get_queue('BaseballSchedule')

# connect to the Batter Results queue for writting results from the individual at-bats

batter_queue = conn.get_queue('BatterResults')

# start functions here

def initialize_game():
    global out, inning, visitor_score, home_score, visitor_batter_up, home_batter_up, visitor_atbat, h_ab, v_ab, h_hit, v_hit

    out = 0
    inning = 1
    visitor_score = 0
    home_score = 0
    visitor_batter_up = 1
    home_batter_up = 1
    visitor_atbat = True

    for i in range(1, 10):
        h_ab[i] = 0
        v_ab[i] = 0
        h_hit[i] = 0
        v_hit[i] = 0

# retrieve team information here based on which team is playing

def get_team_info():
    global home_name, visitor_name

    team_info = boto.connect_s3()

    bucket = team_info.get_bucket('baseballgame')

    from boto.s3.key import Key

    k = Key(bucket)

    team = 'nationals'
    home_name = team

    k.key = team

    s = k.get_contents_as_string()
    x = json.loads(s)

    print 'loading lineup for: ' + team

    h_lineup.append(team)
    h_lineup.append(x[team]['first']['name'])
    h_lineup.append(x[team]['second']['name'])
    h_lineup.append(x[team]['third']['name'])
    h_lineup.append(x[team]['fourth']['name'])
    h_lineup.append(x[team]['fifth']['name'])
    h_lineup.append(x[team]['sixth']['name'])
    h_lineup.append(x[team]['seventh']['name'])
    h_lineup.append(x[team]['eighth']['name'])
    h_lineup.append(x[team]['ninth']['name'])

    h_positions.append(team)
    h_positions.append(x[team]['first']['pos'])
    h_positions.append(x[team]['second']['pos'])
    h_positions.append(x[team]['third']['pos'])
    h_positions.append(x[team]['fourth']['pos'])
    h_positions.append(x[team]['fifth']['pos'])
    h_positions.append(x[team]['sixth']['pos'])
    h_positions.append(x[team]['seventh']['pos'])
    h_positions.append(x[team]['eighth']['pos'])
    h_positions.append(x[team]['ninth']['pos'])

    team = 'giants'
    visitor_name = team

    k.key = team

    s = k.get_contents_as_string()

    x = json.loads(s)

    print 'loading lineup for: ' + team

    v_lineup.append(team)
    v_lineup.append(x[team]['first']['name'])
    v_lineup.append(x[team]['second']['name'])
    v_lineup.append(x[team]['third']['name'])
    v_lineup.append(x[team]['fourth']['name'])
    v_lineup.append(x[team]['fifth']['name'])
    v_lineup.append(x[team]['sixth']['name'])
    v_lineup.append(x[team]['seventh']['name'])
    v_lineup.append(x[team]['eighth']['name'])
    v_lineup.append(x[team]['ninth']['name'])

    v_positions.append(team)
    v_positions.append(x[team]['first']['pos'])
    v_positions.append(x[team]['second']['pos'])
    v_positions.append(x[team]['third']['pos'])
    v_positions.append(x[team]['fourth']['pos'])
    v_positions.append(x[team]['fifth']['pos'])
    v_positions.append(x[team]['sixth']['pos'])
    v_positions.append(x[team]['seventh']['pos'])
    v_positions.append(x[team]['eighth']['pos'])
    v_positions.append(x[team]['ninth']['pos'])

# process logic around an atbat

def process_atbat():
    global at_bat, visitor_batter_up, home_batter_up, visitor_atbat, out, game_inprogress, visitor_pitches_thrown, home_pitches_thrown

    # first create a buffer

    buf = cStringIO.StringIO()

    if visitor_atbat:
        batter = v_lineup[visitor_batter_up]
    else:
        batter = h_lineup[home_batter_up]

    # call the API to process the at-bat

    c = pycurl.Curl()
    c.setopt(c.URL, 'http://ec2-54-148-170-47.us-west-2.compute.amazonaws.com:8080/play?' + batter)
    c.setopt(c.WRITEFUNCTION, buf.write)
    c.perform()

    print 'batter up: ' + batter

    # load the buffer with the json object returned from the API

    res = json.loads(buf.getvalue())

    # parse out the attbitues returned in the object

    if res['outcome'] == 'out':
        at_bat = res['type']
        play_out(at_bat)
    else:
        at_bat = res['hit']
        play_hit(at_bat)

    # clear the buffer for the next batter

    buf.truncate(0)

    # write the result of the atbat out to a queue

    at_bat_queue = conn.get_queue('BatterResults')

    from boto.sqs.message import Message

    ab = Message()

    ab_result = '{"name" : ' + batter + ', "result" : ' + at_bat + '}'

    ab.set_body(ab_result)

    at_bat_queue.write(ab)

    # determine which batter is up next

    if visitor_atbat:
        home_pitches_thrown += res['pitches']
        print 'home pitches thrown: ' + str(home_pitches_thrown)
        v_ab[visitor_batter_up] += 1
        visitor_batter_up += 1
        if visitor_batter_up > 9:
            visitor_batter_up = 1
    else:
        visitor_pitches_thrown += res['pitches']
        print 'visitor pitches thrown: ' + str(visitor_pitches_thrown)
        h_ab[home_batter_up] += 1
        home_batter_up += 1
        if home_batter_up > 9:
            home_batter_up = 1

    # check to see if inning and or game is done

    if out > 2:
        if inning == 9:
            if visitor_atbat:
                inning_change()
            else:
                game_inprogress = False
        else:
            inning_change()

# function to wrap-up the game at the end

def process_final_score():
    global visitor_score, home_score

    visitor_ab = 0
    home_ab = 0
    visitor_hit = 0
    home_hit = 0
    
    print '---------------------------'
    print 'Final Score - ' + visitor_name + ' : ' + str(visitor_score)
    print '              ' + home_name + ' : ' + str(home_score)
    print '---------------------------'

    print '  VISITORS BOX SCORE'

    for i in range(1, 10):
        print v_lineup[i] + ', ' + v_positions[i] + '\t AB ' + str(v_ab[i]) + ' H ' + str(v_hit[i])
        visitor_ab += v_ab[i]
        visitor_hit += v_hit[i]

    print 'TOTAL : AB ' + str(visitor_ab) + ' H ' + str(visitor_hit) 

    print '---------------------------'

    print '   HOME BOX SCORE'
    for i in range(1, 10):
        print h_lineup[i] + ', ' + h_positions[i] + '\t AB ' + str(h_ab[i]) + ' H ' + str(h_hit[i])
        home_ab += h_ab[i]
        home_hit += h_hit[i]

    print 'TOTAL : AB ' + str(home_ab) + ' H ' + str(home_hit)

    print '---------------------------'

    game_queue = conn.get_queue('BaseballGame')

    from boto.sqs.message import Message

    g = Message()

    game_result = '{"visitor" : ' + str(visitor_score) + ', "home" : ' + str(home_score) + '}'

    g.set_body(game_result)

    game_queue.write(g)

# process logic for an out

def play_out(at_bat):
    global out, inning, game_inprogress, visitor_atbat

    print 'Result : ' + at_bat

    out += 1
    print 'Number of outs: %d' % out

# process when an inning changes over, including removing baserunners

def inning_change():
     global out, inning, visitor_atbat, runner_on_first, runner_on_second, runner_on_third

     out = 0

     if visitor_atbat:
         print 'Hometeam now up'
         visitor_atbat = False
     else:
         inning += 1
         print '---------------------------'
         print 'Beginning inning number: %d' % inning
         print '---------------------------'
         print 'Score - ' + visitor_name + ' : ' + str(visitor_score)
         print '        ' + home_name + ' : ' + str(home_score)
         print '---------------------------'
         visitor_atbat = True

     runner_on_first = False
     runner_on_second = False
     runner_on_third = False

# process when an at-bat is a hit

def play_hit(at_bat):
    global visitor_batter_up, home_batter_up, visitor_atbat

    print 'Basehit! : ' + at_bat

    if at_bat == 'single':
        record_single()
    if at_bat == 'double':
        record_double()
    if at_bat == 'triple':
        record_triple()
    if at_bat == 'homerun':
        record_homerun()

    if visitor_atbat:
        v_hit[visitor_batter_up] += 1
    else:
        h_hit[home_batter_up] += 1

# process the logic for a single hit

def record_single():

    global runner_on_first, runner_on_second, runner_on_third, home_score, visitor_score, visitor_atbat

    if runner_on_third:
        print 'Runner scores from third'
        runner_on_third = False
        if visitor_atbat:
            visitor_score += 1
        else:
            home_score += 1
    if runner_on_second:
        print 'Runner moves from second to third'
        runner_on_third = True
        runner_on_second = False
    if runner_on_first:
        print 'Runner moves up to second'
        runner_on_second = True

    runner_on_first = True

    print 'Batter advances to first'

# process the logic for a double

def record_double():

    global runner_on_first, runner_on_second, runner_on_third, visitor_score, home_score, visitor_atbat

    run_batted_in = 0

    if runner_on_third:
        print 'Runner scores from third'
        runner_on_third = False
        run_batted_in += 1
    if runner_on_second:
        print 'Runner scores from second'
        runner_on_second = False
        run_batted_in += 1
    if runner_on_first:
        print 'Runner moves from first to third'
        runner_on_first = False
        runner_on_third = True

    print 'Runner advances to second with a double'

    runner_on_second = True

    if visitor_atbat:
        visitor_score += run_batted_in
    else:
        home_score += run_batted_in

# process the logic for a triple

def record_triple():

    global runner_on_first, runner_on_second, runner_on_third, visitor_score, home_score, visitor_atbat

    run_batted_in = 0

    if runner_on_third:
        print 'Runner scores from third'
        runner_on_third = False
        run_batted_in += 1
    if runner_on_second:
        print 'Runner scores from second'
        runner_on_second = False
        run_batted_in += 1
    if runner_on_first:
        print 'Runner scores from third'
        runner_on_first = False
        run_batted_in += 1

    runner_on_third = True

    if visitor_atbat:
        visitor_score += run_batted_in
    else:
        home_score += run_batted_in

# process the logic for a home run

def record_homerun():

   global runner_on_first, runner_on_second, runner_on_third, visitor_score, home_score, visitor_atbat

   baserunner = 0

   if runner_on_first:
       baserunner += 1
       runner_on_first = False
   if runner_on_second:
       baserunner += 1
       runner_on_second = False
   if runner_on_third:
       baserunner += 1
       runner_on_third = False

   run_batted_in = 1 + baserunner

   if visitor_atbat:
       visitor_score += run_batted_in
   else:
       home_score += run_batted_in

# main processing for the game

get_team_info()

for i in range(1, 2):
    game_inprogress = True
    while (game_inprogress):
        process_atbat()
#        time.sleep(gamespeed)

    process_final_score()

    print 'game ' + str(i)

    initialize_game()

