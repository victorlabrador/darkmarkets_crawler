#!/bin/bash

if [ "$#" -ne 3 ]; then
	echo "Need 2 parameteres: market, number_of_processes, option [0-split and execute, 1-just execute]"
	exit
fi

echo "Starting script for market \"$1\" with \"$2\" processes"
cd /home/XXXX/crawler/

if [ $3 -eq 0 ]; then

	# Configuration stuff
	file="products_${1}.txt"
	num_files=${2}
	echo "This file ${file} into ${num_files}"

	if [ ! -f $file ]; then
		echo "File not found!"
		exit
	fi

	# Work out lines per file.
	total_lines=$(wc -l <${file})
	((lines_per_file = (total_lines + num_files - 1) / num_files))

	# Split the actual file, maintaining lines.
	split --lines=${lines_per_file} -d ${file} products_${1}_ -d --additional-suffix=.txt

	# Debug information
	echo "Total lines     = ${total_lines}"
	echo "Lines  per file = ${lines_per_file}"    
	wc -l products_${1}_*
fi


for ((i=0; i<$2; i++)) 
do
	port=$((9060 + $i))
	file="products_${1}_0${i}.txt"
	echo "Going for \"python3 crawler.py $1 $port $file\""
	python3 crawler.py $1 $port $file	
done
