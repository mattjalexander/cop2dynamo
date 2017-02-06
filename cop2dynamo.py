import csv
import sys

# oer csv mappings  -> SMs DDB

# 0 UPC                                       -> upc
# 1 NAME                                      -> name (gsi)
#                                             -> email
#                                             -> dodid [primary key]
# 2 GRADE                                     -> grade
# 3 LastRatingEnd                             -> last_rating_end
# 4 RatingDue     // doesn't exist for ncoers -> rating_due
# 5 RatingStatus                              -> rating_status
# 6 RatingPeriod                              -> rating_period
# 7 RatingType                                -> rating_type
# 8 Rater                                     -> rater
# 9 IntermediateRater                         -> intermediate_rater
# 10 SeniorRater                              -> senior_rater
# 11 Reviewer  // doesn't exist for oers      -> reviewer
# 12 Notes                                    -> notes{'date': ''}
# 13 Legacy NCOER Comments // may not exist   -> notes{'date-legacyNCOER': ''}

source = r'C:\Users\Matt\Documents\SpiderOak Hive\3-161\S1\evals\oers\20160828_oers.csv'

# initialize dynamo connnection
#dynamodb = boto3.resource('dynamodb')
#table = dynamodb.Table('SMs')

with open(source, newline='') as csvfile:
    type = 'unknown'
    for row in csv.reader(csvfile, delimiter=','):

        # skip the row if it looks like a header.
        # the less we trust the source the cleverer we have to be here.
        if row[0] == 'UPC':
            # id if this is an oer or ncoer
            if row[11] == 'Reviewer':
                type = 'ncoer'
            if row[4] == 'RatingDue'
                type = 'oer'
            print("Dealing with a " + type)
            continue

        # i should probably make an SM object. meh.
        upc = row[0]
        name = row[1]
        grade = row[2]
        last_rating_end = row[3]
        rating_due = row[4] # doesn't exist for ncoers
        rating_status = row[5]
        rating_period = row[6]
        rating_type = row[7]
        rater = row[8]
        intermediate_rater = row[9]
        senior_rater = row[10]
        reviewer = row[11]

        if reviewer == '':
            notes = row[12]

        print("upc: ", upc)
        print("name:", name)
        print("---------")