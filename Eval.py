from enum import Enum

class EvalType(Enum):
    OER = 1
    NCOER = 2
    UNKNOWN = 3

    def __str__(self):
        if self == self.NCOER:
            return "NCOER"
        else:
            return "OER"

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
    UPC = 0              # a
    NAME = 1             # b
    GRADE = 2            # c
    LAST_RATING_END = 3  # d
    RATING_STATUS = 4    # e
    LEGACY_NCOER = 5     # f
    RATING_PERIOD = 6    # g
    RATING_TYPE = 7      # h
    RATER = 8            # i
    SR_RATER = 9         # j
    REVIEWER = 10        # k
    NOTES = 11           # l
    LEGACY_NOTES = 12    # n

class Eval:
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
    type = EvalType.UNKNOWN

    def __init__(self):
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
        type = EvalType.UNKNOWN

    def __str__(self):
        stringy = self.grade + " " + self.name + "(" + self.upc + ")'s last rating ended " + str(self.last_rating_end) + "\n"
        stringy = stringy + "The " + self.rating_type + " eval is due on " + str(self.rating_due) + " for " + self.rating_period + ".\n"
        stringy = stringy + "It's " + str(self.rating_status) + "\n"  # + " with " + str(self.rating_due - datetime.now()) + " days left.\n"
        if self.type == EvalType.OER:
            stringy = stringy + self.rater + ", " + self.int_rater + ", and " + self.sr_rater + " are on the hook.\n"
        else:
            stringy = stringy + self.rater + ", " + self.sr_rater + ", and " + self.reviewer + " are on the hook.\n"
        stringy = stringy + self.notes + " " + self.legacy_notes + "\n"

        stringy = stringy + "---------\n"

        return stringy

    # ??? still getting  '<' not supported between instances of 'Eval' and 'Eval'
    def __cmp__(self, other):
        if self.name < other.name:  # compare name value (should be unique)
            return -1
        elif self.name > other.name:
            return 1
        else:
            return 0  # should mean it's the same instance

    def __repr__(self):
        return self.name + "(due on " + str(self.rating_due).partition(' ')[0] + ")\n"

    def table(self):
        return [self.upc, self.grade, self.name, self.rating_status, str(self.rating_due).partition(' ')[0], self.notes]

    def simple_table(self):
        return [self.name, self.rating_status]
