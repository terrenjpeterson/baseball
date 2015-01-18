baseball
========

testing out different AWS features using baseball game

atbat.js is an API written in nodeJS that simulates an at-bat based on a player name provided in the URI

to call the API, use GET /play?<batter last name>, and a json response will provide the result of the at-bat

currently teams hitting data that are processed by the API are as follows:
- giants.json 
- nationals.json

the driver for the program is a python script playball.py that contains the rules for the game, and uses the API above

the lineups used for the game are fetched from an S3 bucket

once the game is completed, the results are written to an SQS queue for analysis

