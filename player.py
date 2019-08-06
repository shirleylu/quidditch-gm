# ranks: (score, confidence)
# input:
# score: 1-5 (1 highest)
# confidence: 1-3 (1 highest)

class Player():
    def __init__(self, name, gender, primaryp, secondaryp, cursor):
        self.name = name
        in_db = self.has_player(self, cursor)

        if not in_db:
            self.add_player(self, cursor)
            in_db = self.has_player(self, cursor)

        self.gender = gender
        self.primaryP = primaryp
        self.secondaryP = secondaryp

    def add_player(name, gender, primaryp, secondaryp, cursor):
        beater = 0
        chaser = 0
        keeper = 0
        seeker = 0

        if secondaryp == "beater":
            beater = 2
        elif secondaryp == "chaser":
            chaser = 2
        elif secondaryp == "keeper":
            keeper = 2
        elif secondaryp == "seeker":
            seeker = 2

        if primaryp == "beater":
            beater = 1
        elif primaryp == "chaser":
            chaser = 1
        elif primaryp == "keeper":
            keeper = 1
        elif primaryp == "seeker":
            seeker = 1

        cursor.execute(
            "insert into player (name, gender, beater, chaser, keeper, seeker) values ('%s','%s', %d, %d, %d, %d)"
            % name, gender, beater, chaser, keeper, seeker)

    def has_player(self, cursor):
        cursor.execute("select * from players where name = '%s'" % self.name)
        return cursor.fetchone()

# def addRank(self, score, confidence):
# 	self.ranks.append((score, confidence))
# 	calculateRunningRank(self)
#
# # this inverts the inputted ranks:
# # score: 5-1 (5 highest)
# # confidence: 3-1 (3 highest)
# # resulting in a 15-1 range (15 highest)
# def calculateRunningRank(self):
# 	if (len(self.ranks) < 1) :
# 		return
# 	flipped = map(lambda(x,y): (6-x, 4-y), self.ranks)
# 	weightedRanks = map(lambda(x,y): x*y, self.flipped)
# 	ranks = reduce(lambda x,y : x+y, weightRanks) / len(self.ranks)

