import csv
import sys
from datetime import datetime, timedelta

import Eval
from os.path import basename
import plotly.offline as offline
from plotly.figure_factory import create_table
import plotly.graph_objs as go

def fix_rating_due(last_rating_end, rating_period):
    #if last_rating_end != '':
    #    return datetime.strptime(rating_period.strip()[-8:], "%Y%m%d") + timedelta(days = 365)
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
    if "submitted to hqda" in notes.lower() or \
       "hqda submitted" in notes.lower() or \
       "hqdq submitted" in notes.lower() or \
       "hqda submittrd" in notes.lower() or \
       "sent to hqda" in notes.lower() or \
       "hqda level" in notes.lower() or \
       "accepted by iperms" in notes.lower() or \
       "iperms accepted" in notes.lower():
        rating_status = "Submitted"
    elif rating_due == '':  # this is mostly to short-circuit.
                            # we default to Unknown anyways
        rating_status = "Unknown"
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
    #source = r'C:\Users\Matt\Documents\SpiderOak Hive\3-161\S1\evals\oers\20170210_oers.csv'
    # source = r'C:\Users\Matt\Documents\SpiderOak Hive\3-161\S1\evals\ncoers\20170106_ncoers.csv'
    #source = r'C:\Users\Matt\Documents\SpiderOak Hive\3-161\S1\evals\ncoers\20170211_ncoers.csv'

    #source = r'/Users/mattalex/SpiderOak Hive/3-161/S1/evals/ncoers/20170211_ncoers.csv'
    source = r'/Users/mattalex/SpiderOak Hive/3-161/S1/evals/ncoers/20170228_ncoers.csv'
    #source = r'/Users/mattalex/SpiderOak Hive/3-161/S1/evals/oers/20170228_oers.csv'
    read_csv(source)

def printme(x):
    returnme = ''
    for x in x:
        returnme = returnme + str(x) + '\n'

def read_csv(source):

    # initialize dynamo connnection
    # dynamodb = boto3.resource('dynamodb')
    # table = dynamodb.Table('SMs')

    total = 0
    unknown = list()
    delinquent = list()
    current = list()
    upcoming = list()
    due = list()
    submitted = list()
    type = Eval.EvalType.UNKNOWN

    with open(source, newline='') as csvfile:
        for row in csv.reader(csvfile, delimiter=','):
            #
            # Basic initialization, mainly figuring out what type of eval report we have.
            #

            if row[0].strip() == 'UPC':
                # id if this is an oer or ncoer
                if row[10].strip() == 'Reviewer':
                    type = Eval.EvalType.NCOER
                elif row[4].strip() == 'RatingDue':
                    type = Eval.EvalType.OER
                else:
                    print("Am I taking crazy pills?")
                print("Dealing with a " + str(type))
                continue

            #
            # Now we'll read from the CSV and populate our internal understanding of the world.
            #
            me = Eval.Eval()
            me.type = type
            if type == Eval.EvalType.OER:
                me.upc = row[Eval.OerFields.UPC.value]
                me.name = row[Eval.OerFields.NAME.value]
                me.grade = row[Eval.OerFields.GRADE.value]
                me.last_rating_end = datetime.strptime(row[Eval.OerFields.LAST_RATING_END.value], "%m/%d/%y")
                me.rating_due = datetime.strptime(row[Eval.OerFields.RATING_DUE.value], "%m/%d/%y")
                me.rating_status = row[Eval.OerFields.RATING_STATUS.value]
                me.rating_period = row[Eval.OerFields.RATING_PERIOD.value]
                me.rating_type = row[Eval.OerFields.RATING_TYPE.value]
                me.rater = row[Eval.OerFields.RATER.value]
                me.int_rater = row[Eval.OerFields.INT_RATER.value]
                me.sr_rater = row[Eval.OerFields.SR_RATER.value]
                me.notes = row[Eval.OerFields.NOTES.value]
            elif type == Eval.EvalType.NCOER:
                me.type = type
                me.upc = row[Eval.NcoerFields.UPC.value]
                me.name = row[Eval.NcoerFields.NAME.value]
                me.grade = row[Eval.NcoerFields.GRADE.value]
                try:
                    me.last_rating_end = datetime.strptime(row[Eval.NcoerFields.LAST_RATING_END.value], "%m/%d/%Y")
                except ValueError:
                    pass
                # parse rating_due from rating_period
                me.legacy_ncoer = row[Eval.NcoerFields.LEGACY_NCOER.value]
                me.rating_status = row[Eval.NcoerFields.RATING_STATUS.value]
                me.rating_period = row[Eval.NcoerFields.RATING_PERIOD.value]
                me.rating_type = row[Eval.NcoerFields.RATING_TYPE.value]
                me.rater = row[Eval.NcoerFields.RATER.value]
                # no int_rater for ncoers
                me.sr_rater = row[Eval.NcoerFields.SR_RATER.value]
                me.reviewer = row[Eval.NcoerFields.REVIEWER.value]
                me.notes = row[Eval.NcoerFields.NOTES.value]
                try:
                    me.notes = me.notes + row[Eval.NcoerFields.LEGACY_NOTES.value]
                except IndexError:
                    pass
            else:
                sys.exit("Unknown type: " + str(type))

            #
            # Massage the data.
            # if you don't have a rating period, you can derive what it probably
            # is from LastRatingDue and assuming an annual
            if me.rating_period == '' and me.last_rating_end != '':
                (me.rating_period, me.rating_type) = fix_rating_period(me.last_rating_end)

            # similarly, we can derive the rating_end from the rating period if
            # we're not explicitly given it
            if me.rating_due == '' and me.rating_period != '':
                me.rating_due = fix_rating_due(me.last_rating_end, me.rating_period)

            me.rating_status = fix_rating_status(datetime.strptime(basename(source)[:8], "%Y%m%d"), me.rating_due, me.notes)
            total = total + 1

            #
            # Update statistics
            #
            if me.rating_status == "Delinquent":
                delinquent.append(me)

            if "Unknown" in me.rating_status:
                unknown.append(me)

            if me.rating_status == "Current":
                current.append(me)

            if me.rating_status == "Upcoming":
                upcoming.append(me)

            if me.rating_status == "Due":
                due.append(me)

            if me.rating_status == "Submitted":
                submitted.append(me)

    print("Total: " + str(total))

    #print("Submitted: " + str(submitted.__len__()) + ": " + str(submitted))
    #print("Delinquent: " + str(delinquent.__len__()) + ": " + str(delinquent))
    #print("Due: " + str(due.__len__()) + ": " + str(due))
    #print("Upcoming: " + str(upcoming.__len__()) + ": " + str(upcoming))
    #print("Current: " + str(current.__len__()) + ": " + str(current))
    #print("Unknown: " + str(unknown.__len__()) + ": " + str(unknown))

    # build by-name list over NCOERs that need action
    for unit in "PAPA0", "PAPB0", "PAPC0", 'PAPT0', "QYTJ0":
        # print("     Delinquent: " + str([x for x in delinquent if x.upc == unit]))
        # print("     Due: " + str([x for x in due if x.upc == unit]))
        # print("     Upcoming: " + str([x for x in upcoming if x.upc == unit]))
        # print("     Current: " + str([x for x in current if x.upc == unit]))
        # print("     Unknown: " + str([x for x in unknown if x.upc == unit]))

        table = (#[x.table() for x in submitted if x.upc == unit] +
                 [x.table() for x in delinquent if x.upc == unit] +
                 [x.table() for x in due if x.upc == unit] +
                 [x.table() for x in upcoming if x.upc == unit] +
                 [x.table() for x in unknown if x.upc == unit]
                 #[x.table() for x in current if x.upc == unit]
                 )

        # plotly prints tables like hot garbage. print it, then copy into excel.
        base=r'/Users/mattalex/SpiderOak Hive/3-161/S1/evals'
        #with open(base + '/' + unit + '_' + str(me.type) +'.csv', 'w', newline='') as csvfile:
        with open(base + '/' + '20170228_' + unit + '.csv', 'a', newline='') as csvfile:
            spamwriter = csv.writer(csvfile, delimiter=',')
            for row in table:
                spamwriter.writerow(row)

        #if table:
        #    table.insert(0, ["Name", "Status", "Due", "Notes"])
        #    figure2 = create_table(table)
        #figure2.layout.width = 1500  # width in pixels
        #figure2.layout.margin.update({'t': 75, 'l': 50})  # make room for the title
        #figure2.layout.update({'title': unit + " " + basename(source)[:8] + " " + str(type) + " By Name List"})
        #for i in range(len(figure2.layout.annotations)):
        #    figure2.layout.annotations[i].font.size = 8
        #offline.plot(figure2, filename=unit + '.html',
        #             #image_filename=unit + '.png',
        #             image='png')

        #print("     Submitted: " + str([x for x in submitted if x.upc == unit]))
        #print("     Delinquent: " + str([x for x in delinquent if x.upc == unit]))
        #print("     Due: " + str([x for x in due if x.upc == unit]))
        #print("     Upcoming: " + str([x for x in upcoming if x.upc == unit]))
        #print("     Current: " + str([x for x in current if x.upc == unit]))
        #print("     Unknown: " + str([x for x in unknown if x.upc == unit]))

    # build statistics table
    # seems pretty absurdly inefficient, i'm filtering the same 7 lists 5 different times
    data_matrix = [['Unit','Submitted', 'Delinquent', 'Due', 'Upcoming', 'Current', 'Unknown'],
                   ['A Co', [x for x in submitted if x.upc == 'PAPA0'].__len__(),
                            [x for x in delinquent if x.upc == 'PAPA0'].__len__(),
                            [x for x in due if x.upc == 'PAPA0'].__len__(),
                            [x for x in upcoming if x.upc == 'PAPA0'].__len__(),
                            [x for x in current if x.upc == 'PAPA0'].__len__(),
                            [x for x in unknown if x.upc == 'PAPA0'].__len__()],
                   ['B Co', [x for x in submitted if x.upc == 'PAPB0'].__len__(),
                    [x for x in delinquent if x.upc == 'PAPB0'].__len__(),
                    [x for x in due if x.upc == 'PAPB0'].__len__(),
                    [x for x in upcoming if x.upc == 'PAPB0'].__len__(),
                    [x for x in current if x.upc == 'PAPB0'].__len__(),
                    [x for x in unknown if x.upc == 'PAPB0'].__len__()],
                   ['C Co', [x for x in submitted if x.upc == 'PAPC0'].__len__(),
                    [x for x in delinquent if x.upc == 'PAPC0'].__len__(),
                    [x for x in due if x.upc == 'PAPC0'].__len__(),
                    [x for x in upcoming if x.upc == 'PAPC0'].__len__(),
                    [x for x in current if x.upc == 'PAPC0'].__len__(),
                    [x for x in unknown if x.upc == 'PAPC0'].__len__()],
                   ['HHC', [x for x in submitted if x.upc == 'PAPT0'].__len__(),
                    [x for x in delinquent if x.upc == 'PAPT0'].__len__(),
                    [x for x in due if x.upc == 'PAPT0'].__len__(),
                    [x for x in upcoming if x.upc == 'PAPT0'].__len__(),
                    [x for x in current if x.upc == 'PAPT0'].__len__(),
                    [x for x in unknown if x.upc == 'PAPT0'].__len__()],
                   ['I Co', [x for x in submitted if x.upc == 'QYTJ0'].__len__(),
                    [x for x in delinquent if x.upc == 'QYTJ0'].__len__(),
                    [x for x in due if x.upc == 'QYTJ0'].__len__(),
                    [x for x in upcoming if x.upc == 'QYTJ0'].__len__(),
                    [x for x in current if x.upc == 'QYTJ0'].__len__(),
                    [x for x in unknown if x.upc == 'QYTJ0'].__len__()],
                   ['TOTAL', submitted.__len__(),
                             delinquent.__len__(),
                             due.__len__(),
                             upcoming.__len__(),
                             current.__len__(),
                             unknown.__len__()]]

    trace = go.Pie(labels=["Submitted", "Delinquent", "Due", "Upcoming", "Current", "Unknown"],
                   values=[submitted.__len__(), delinquent.__len__(), due.__len__(),
                           upcoming.__len__(), current.__len__(), unknown.__len__()],
                   marker={'colors': ['blue',  # submitted
                                    'black', # delinquent
                                    'red',   # due
                                    'yellow', # upcoming
                                    'green', # current
                                    'grey']}, # unknown
                   domain= {'x': [.6, 1],
                            'y': [0, 1]},
                   hoverinfo='label+percent',
                   showlegend=False,
                   textinfo='label+percent',
                   name='Evals')

    figure = create_table(data_matrix)
    figure['data'].extend(go.Data([trace]))
    figure.layout.xaxis.update({'domain': [0, .7]})
    figure.layout.margin.update({'t': 75, 'l': 50}) # make room for the title
    figure.layout.update({'title': basename(source)[:8] + " " + str(type) + " Snapshot"})
    figure.layout.update({'height': 350})
    offline.plot(figure, filename='snapshot.html', image_filename='snapshot.png', image='png')

if __name__ == "__main__":
    main()