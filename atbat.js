// atbat
// include the required node.js packages

var express = require('express');
var http = require('http');
var fs = require('fs');
var Chance = require('chance');
var math = require('mathjs');

var NATIONALS_DATA_FILE = "nationals.json";
var GIANTS_DATA_FILE = "giants.json";

// establish global variables

var hitting_array = [];

var average = 250;

var hits = 150;
var homerun = 10;
var triples = 4;
var doubles = 20;

var strikeout_average = .35;
var groundout_average = .25;

// create the server

var app = express();

var server = http.createServer(app);

console.log('loading batting data');

var nationals_data = fs.readFileSync(NATIONALS_DATA_FILE, 'utf8');
var nationals_array = eval('('+ nationals_data + ')');

console.log('loading nationals hitters');

for (var i = 0; i < nationals_array.length; i++)
  {console.log('batter info: ' + JSON.stringify(nationals_array[i]));
   hitting_array.push(nationals_array[i]);}

var giants_data = fs.readFileSync(GIANTS_DATA_FILE, 'utf8');
var giants_array = eval('('+ giants_data + ')');

console.log('loading giants hitters');

for (var i = 0; i < giants_array.length; i++)
  {console.log('batter info: ' + JSON.stringify(giants_array[i]));
   hitting_array.push(giants_array[i]);}

// the logic for the api

app.get('/play', function(req, res){

//    console.log('play API called' + req.url);

    batter = {};
    batter.name = req.url.slice(6, req.url.length);

    // these are the default values

    batter.average = average;
    batter.hits    = hits;
    batter.homerun = homerun;
    batter.triples = triples;
    batter.doubles = doubles;

    // check the array of hitters to find specific attributes to set

    for (var i = 0; i < hitting_array.length; i++)
      {
       if (batter.name == hitting_array[i].name)
         {
          batter.homerun = hitting_array[i].homeruns;
          batter.doubles = hitting_array[i].doubles;
          batter.triples = hitting_array[i].triples;
          batter.average = hitting_array[i].average;
          batter.hits    = hitting_array[i].hits;
         }
      }

    // these are the same for all batters

    batter.strikeout_average = strikeout_average;
    batter.groundout_average = groundout_average;

    atBat(batter, res);

});

app.get('/index.html', function(req, res){

    console.log('index page hit');

    res.send();

});

function atBat(batter, res) {

  console.log('batter stats : ' + JSON.stringify(batter));

  var chance = new Chance();

  var my_random_int = chance.integer({min: 1, max: 1000});

  var pitches_thrown = chance.integer({min: 1, max: 8});

  var result = {};
      result.random  = my_random_int;
      result.pitches = pitches_thrown;

  var homerun_range = math.round(batter.average * (batter.homerun/batter.hits), 0);
  var triple_range = math.round(batter.average * (batter.triples/batter.hits) + homerun_range, 0);
  var double_range = math.round(batter.average * (batter.doubles/batter.hits) + triple_range, 0);

  var strikeout_range = math.round(strikeout_average * (1000 - batter.average) + batter.average, 0);
  var groundout_range = math.round(groundout_average * (1000 - batter.average) + strikeout_range, 0);

  if (my_random_int < batter.average)
    {
     // process the result of a basehit

     result.outcome = 'basehit';

     if (my_random_int < homerun_range)
       result.hit = 'homerun'
     else
       if (my_random_int < triple_range)
         result.hit = 'triple'
       else
         if (my_random_int < double_range)
           result.hit = 'double'
         else
           result.hit = 'single';
    }
  else
    {
     // process the result of an out

     result.outcome = 'out';

     if (my_random_int < strikeout_range)
       result.type = 'strikeout'
     else if
        (my_random_int < groundout_range)
       result.type = 'groundout'
     else
       result.type = 'flyout';
    };

  // respond with the result of the atbat

  res.send(result);

};

// begin listening on the port for traffic

console.log('server starting');

app.listen(8080);
