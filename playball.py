# connect to SQS to gather data for at-bats

import boto.sqs
conn = boto.sqs.connect_to_region("us-west-2")

import time
import json

# initialize global variables to begin the game

gamespeed = 0.01
out = 0
inning = 1
visitor_score = 0
home_score = 0

h_ab = [0] * 10
v_ab = [0] * 10

h_hit = [0] * 10
v_hit = [0] * 10

h_lineup = []
v_lineup = []

visitor_batter_up = 1
home_batter_up = 1

visitor_atbat = True
game_inprogress = True

runner_on_first = False
runner_on_second = False
runner_on_third = False

# connect to the AtBat queue that has simulations predefined

my_queue = conn.get_queue('AtBat')

# start functions here

# retrieve team information here based on which team is playing

def get_team_info():

    team = 'nationals'

    team_info = boto.connect_s3()

    bucket = team_info.get_bucket('baseballgame')

    from boto.s3.key import Key

    k = Key(bucket)
    k.key = team

    s = k.get_contents_as_string()
    x = json.loads(s)

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

    print h_lineup[1], h_lineup[2], h_lineup[3]
    print h_lineup[4], h_lineup[5], h_lineup[6]
    print h_lineup[7], h_lineup[8], h_lineup[9]

# process logic around an atbat

def process_atbat():
    global at_bat, gamespeed, visitor_batter_up, home_batter_up, visitor_atbat

    m = my_queue.read()
    x = m.get_body()
    y = json.loads(x)

    at_bat = y['atbat']

    if at_bat == 'strikeout':
        play_out(at_bat)
    elif at_bat == 'groundout':
        play_out(at_bat)
    elif at_bat == 'flyout':
        play_out(at_bat)
    else:
        play_hit(at_bat)

    if visitor_atbat:
        print 'visitor batter : ' + str(visitor_batter_up)
        v_ab[visitor_batter_up] += 1
        visitor_batter_up += 1
        if visitor_batter_up > 9:
            visitor_batter_up = 1
    else:
        print 'home batter : ' + str(home_batter_up)
        h_ab[home_batter_up] += 1
        home_batter_up += 1
        if home_batter_up > 9:
            home_batter_up = 1

    time.sleep(gamespeed)

    my_queue.delete_message(m)

# wrap-up the game at the end

def process_final_score():
    global visitor_score, home_score

    visitor_ab = 0
    home_ab = 0
    visitor_hit = 0
    home_hit = 0
    
    print '---------------------------'
    print 'Final Score - Visitor %d ' % visitor_score
    print '              Home %d ' % home_score
    print '---------------------------'

    print '  VISITORS BOX SCORE'

    for i in range(1, 10):
        print 'batter ' + str(i) + ' AB ' + str(v_ab[i]) + ' H ' + str(v_hit[i])
        visitor_ab += v_ab[i]
        visitor_hit += v_hit[i]

    print 'TOTAL : AB ' + str(visitor_ab) + ' H ' + str(visitor_hit) 

    print '---------------------------'

    print '   HOME BOX SCORE'
    for i in range(1, 10):
        print h_lineup[i] + '\t' + str(i) + ' AB ' + str(h_ab[i]) + ' H ' + str(h_hit[i])
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

    if out == 3:
        if inning == 9:
            if visitor_atbat:
                inning_change()
            else:
                process_final_score()
                game_inprogress = False
        else:
            inning_change()

# process when an inning changes over, including removing baserunners

def inning_change():
     global out, inning, visitor_atbat, runner_on_first, runner_on_second, runner_on_third

     print 'Inning change'
     out = 0

     if visitor_atbat:
         print 'Hometeam now up'
         visitor_atbat = False
     else:
         inning += 1
         print '---------------------------'
         print 'Beginning inning number: %d' % inning
         print '---------------------------'
         print 'Score - Visitor %d ' % visitor_score
         print '        Home %d ' % home_score
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

   print 'Score Visitor %d ' % visitor_score
   print '      Home %d ' % home_score
      
# main processing for the game

get_team_info()

while (game_inprogress):
    process_atbat()
