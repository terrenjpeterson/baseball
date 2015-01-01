// atbat
// include the required node.js packages

var express = require('express');
var http = require('http');
//var connect = require('connect');
var fs = require('fs');
var Chance = require('chance');
var math = require('mathjs');

// establish global variables

var average = 300;

var hits = 190;
var homerun = 30;
var triples = 9;
var doubles = 23;

var strikeout_average = .35;
var groundout_average = .25;

// create the server

var app = express();

var server = http.createServer(app);

// the logic for the api

console.log('loading routes');

app.get('/play', function(req, res){

    batter = {};
    batter.average = average;
    batter.hits = hits;
    batter.homerun = homerun;
    batter.triples = triples;
    batter.doubles = doubles;
    batter.strikeout_average = strikeout_average;
    batter.groundout_average = groundout_average;

    console.log('play API called' + req.url);

    console.log(req.url.slice(6, req.url.length));

    atBat(batter, res);

});

function atBat(batter, res) {

  console.log('batter is : ' + batter.average);

  var chance = new Chance();

  var my_random_int = chance.integer({min: 1, max: 1000});

  var result = {};
      result.random = my_random_int;

  var homerun_range = math.round(average * (homerun/hits), 0);
  var triple_range = math.round(average * (triples/hits) + homerun_range, 0);
  var double_range = math.round(average * (doubles/hits) + triple_range, 0);

  var strikeout_range = math.round(strikeout_average * (1000 - average) + average, 0);
  var groundout_range = math.round(groundout_average * (1000 - average) + strikeout_range, 0);

  if (my_random_int < average)
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

  console.log(result);

  res.send(result);

};

// begin listening on the port for traffic

app.listen(8080);
