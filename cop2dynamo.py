import csv
import sys

# expectec columns for oers
# 20170131_oers.csv:
# UPC
# NAME
# GRADE
# LastRatingEnd
# RatingDue
# RatingStatus
# RatingPeriod
# RatingType
# Rater
# IntermediateRater
# SeniorRater
# Notes
source_dir = r'C:\Users\Matt\Documents\SpiderOak Hive\3-161\S1\evals\oers'

# Table: SMs
# attributes:
#   RatingBegin
#   RatingEnd
#   Unit
#   Rater
#   Sr. Rater
#   Rank
#   RatingType
#   Comments: {'date': ''}

# initialize dynamo connnection
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('SMs')

with open(source, newline='') as csvfile:
    for row in csv.reader(csvfile, delimiter=','):
        # skip the row if it looks like a header.
        # the less we trust the source the cleverer we have to be here.
        if row[1] == 'DODID':
            continue

        # apparently some people don't have email. that's ok i guess.
        # (nb: dynamo isn't happy at empty values)
        if row[2] == '':
            row[2] = '.'

        # Update dynamo.
        table.put_item(Item={
            'name': row[0],
            'DODID': row[1],
            'email': row[2]
            })