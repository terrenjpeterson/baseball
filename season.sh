#!/bin/bash
# run a large set of games

for i in  {1..100}
do
    echo $i
    python playball.py
done
