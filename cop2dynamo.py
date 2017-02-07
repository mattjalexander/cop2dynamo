from enum import Enum
import csv
import sys
from datetime import datetime, timedelta

class EvalType(Enum):
    OER = 1
    NCOER = 2
    UNKNOWN = 3

# Maps to the expected column in the csv
class OerFields(Enum):
    UPC = 0
    NAME = 1
    GRADE = 2
    LAST_RATING_END = 3
    RATING_DUE = 4
    RATING_STATUS = 5
    RATING_PERIOD = 6
    RATING_TYPE = 7
    RATER = 8
    INT_RATER = 9
    SR_RATER = 10
    NOTES = 11

class NcoerFields(Enum):
    UPC = 0
    NAME = 1
    GRADE = 2
    LAST_RATING_END = 3
    RATING_STATUS = 4
    LEGACY_NCOER = 5
    RATING_PERIOD = 6
    RATING_TYPE = 7
    RATER = 8
    SR_RATER = 9
    REVIEWER = 10
    NOTES = 11
    LEGACY_NOTES = 12

def fix_rating_due(rating_period):
    if rating_period == '':
        return ''
    return datetime.strptime(rating_period.strip()[-8:], "%Y%m%d")

def fix_rating_period(last_rating_end):
    if last_rating_end != '':
        begin = last_rating_end + timedelta(days = 1)
        end = begin + timedelta(days = 365)
        return (begin.strftime("%Y%m%d") + "-" + end.strftime("%Y%m%d"), "ANNUAL")

# We do read this in, but we also don't trust it. It only says "Current, Due, or Delinquent.", and
# is often incorrect
# Statuses:
#   Unknown (no data),
#   Current (60+ days out),
#   Upcoming (60 days out),
#   Due (0-30 days overdue),
#   Delinquent (31+ days overdue),
#   Submitted if Notes has the word submitted in it
def fix_rating_status(mytime, rating_due, notes):
    if "submitted" in notes.lower() or "sent to hqda" in notes.lower():
        rating_status = "Submitted"
    elif rating_due == '':  # this is mostly to short-circuit.
                            # we default to Unknown anyways
        rating_status = "Unknown, no RatingDue"
    elif ((rating_due - mytime) > timedelta(days=60)):
        rating_status = "Current"
    elif ((rating_due - mytime) > timedelta(days=1)):
        rating_status = "Upcoming"
    elif ((rating_due - mytime) > timedelta(days=-29)):
        rating_status = "Due"
    elif ((rating_due - mytime) <= timedelta(days=-30)):
        rating_status = "Delinquent"
    else:
        rating_status = "Unknown. Days left: " + str(rating_due - mytime)

    return rating_status


def main():
    # source = r'C:\Users\Matt\Documents\SpiderOak Hive\3-161\S1\evals\oers\20160828_oers.csv'
    source = r'C:\Users\Matt\Documents\SpiderOak Hive\3-161\S1\evals\ncoers\20170106_ncoers.csv'

    # initialize dynamo connnection
    # dynamodb = boto3.resource('dynamodb')
    # table = dynamodb.Table('SMs')

    with open(source, newline='') as csvfile:
        type = EvalType.UNKNOWN
        for row in csv.reader(csvfile, delimiter=','):
            #
            # Basic initialization, mainly figuring out what type of eval report we have.
            #

            if row[0].strip() == 'UPC':
                # id if this is an oer or ncoer
                if row[10].strip() == 'Reviewer':
                    type = EvalType.NCOER
                if row[4].strip() == 'RatingDue':
                    type = EvalType.OER
                print("Dealing with a " + str(type))
                continue

            #
            # Now we'll read from the CSV and populate our internal understanding of the world.
            #

            # initialize
            upc = ''
            name = ''
            grade = ''
            last_rating_end = ''
            rating_due = ''
            rating_status = ''
            rating_period = ''
            rating_type = ''
            rater = ''
            int_rater = ''
            sr_rater = ''
            reviewer = ''
            notes = ''
            legacy_notes = ''

            if type == EvalType.OER:
                # i should probably make an SM object. meh.
                upc = row[OerFields.UPC.value]
                name = row[OerFields.NAME.value]
                grade = row[OerFields.GRADE.value]
                last_rating_end = datetime.strptime(row[OerFields.LAST_RATING_END.value], "%m/%d/%Y")
                rating_due = datetime.strptime(row[OerFields.RATING_DUE.value], "%m/%d/%Y")
                rating_status = row[OerFields.RATING_STATUS.value]
                rating_period = row[OerFields.RATING_PERIOD.value]
                rating_type = row[OerFields.RATING_TYPE.value]
                rater = row[OerFields.RATER.value]
                int_rater = row[OerFields.INT_RATER.value]
                sr_rater = row[OerFields.SR_RATER.value]
                notes = row[OerFields.NOTES.value]
            elif type == EvalType.NCOER:
                upc = row[NcoerFields.UPC.value]
                name = row[NcoerFields.NAME.value]
                grade = row[NcoerFields.GRADE.value]
                try:
                    last_rating_end = datetime.strptime(row[NcoerFields.LAST_RATING_END.value], "%m/%d/%Y")
                except ValueError:
                    pass
                # parse rating_due from rating_period
                legacy_ncoer = row[NcoerFields.LEGACY_NCOER.value]
                rating_status = row[NcoerFields.RATING_STATUS.value]
                rating_period = row[NcoerFields.RATING_PERIOD.value]
                rating_type = row[NcoerFields.RATING_TYPE.value]
                rater = row[NcoerFields.RATER.value]
                # no int_rater for ncoers
                sr_rater = row[NcoerFields.SR_RATER.value]
                reviewer = row[NcoerFields.REVIEWER.value]
                notes = row[NcoerFields.NOTES.value]
                try:
                    legacy_notes = row[NcoerFields.LEGACY_NOTES.value]
                except IndexError:
                    pass
            else:
                sys.exit("Unknown type: " + str(type))

            #
            # Massage the data.
            # if you don't have a rating period, you can derive what it probably
            #
            # is from LastRatingDue and assuming an annual
            if rating_period == '' and last_rating_end != '':
                (rating_period, rating_type) = fix_rating_period(last_rating_end)

            # similarly, we can derive the rating_end from the rating period if
            # we're not explicitly given it
            if rating_due == '' and rating_period != '':
                rating_due = fix_rating_due(rating_period)

            rating_status = fix_rating_status(datetime.now(), rating_due, notes)

            #
            # Do something with these random variables.
            #
            print(grade + " " + name + "(" + upc + ")'s last rating ended " + str(last_rating_end))
            print("The " + rating_type + " eval is due on " + str(rating_due) + " for " + rating_period + ".")
            print("It's " + str(rating_status))# + " with " + str(rating_due - datetime.now()) + " days left.")
            if type == EvalType.OER:
                print(rater + ", " + int_rater + ", and " + sr_rater + " are on the hook.")
            else:
                print(rater + ", " + sr_rater + ", and " + reviewer + " are on the hook.")
            print(notes + " " + legacy_notes)

            print("---------")

if __name__ == "__main__":
    main()