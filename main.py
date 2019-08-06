import csv
import sqlite3

conn = sqlite3.connect('test.db')
cursor = conn.cursor()

PLAYERS = {}
CSV_PATHS = ["./example.csv"]

RANKING = "Ranking"
CONFIDENCE = "Confidence"
FIRST_NAME = "Name (First)"
LAST_NAME = "Name (Last)"
GENDER = "Gender:"
PRIMARY_POSITION = "Primary position:"
SECONDARY_POSITION = "Secondary position:"


class Player:
    def __init__(self, name, gender, primaryp, secondaryp):
        in_db = self.has_player(name)

        if not in_db:
            self.add_player(name, gender, primaryp, secondaryp)

        # self.gender = gender
        # self.primaryP = primaryp
        # self.secondaryP = secondaryp

    def add_player(self, name, gender, primaryp, secondaryp):
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

        gender.strip()
        gender = gender.replace("'", "")
        # print("insert into players (name, gender, beater, chaser, keeper, seeker) values ('%s','%s', %d, %d, %d, %d)"
        #     % (name, gender, beater, chaser, keeper, seeker))
        cursor.execute(
            "insert into players (name, gender, beater, chaser, keeper, seeker) values ('%s','%s', %d, %d, %d, %d)"
            % (name, gender, beater, chaser, keeper, seeker))

    def has_player(self, name):
        cursor.execute("select * from players where name = '%s'" % name)
        return cursor.fetchone()


class Rank:
    def __init__(self, name, ranking, confidence):
        id = self.lookup_player(name)
        self.add_rank(id, ranking, confidence)

    def lookup_player(self, name):
        cursor.execute("select id from players where name = '%s'" % name)
        return cursor.fetchone()[0]

    def add_rank(self, id, ranking, confidence):
        ranking = float(ranking)
        confidence = float(confidence)
        cursor.execute(
            "insert into ranks (playerid, rank, confidence, weightedRank) values (%d, %d, %d, %d)"
            % (id, ranking, confidence, self.calculate_weighted_rank(ranking, confidence)))

    def calculate_weighted_rank(self, ranking, confidence):
        return (6 - ranking) * (4 - confidence)


def parse_input(files):
    for file in files:
        with open(file) as csv_file:
            csv_reader = csv.reader(csv_file)
            header = None
            for row in csv_reader:
                if not header:
                    header = row
                    continue
                name = row[header.index(FIRST_NAME)] + row[header.index(LAST_NAME)]
                name.strip()
                gender = row[header.index(GENDER)].lower()

                ranking = row[header.index(RANKING)]
                confidence = row[header.index(CONFIDENCE)]

                primaryp = row[header.index(PRIMARY_POSITION)].lower()
                secondaryp = row[header.index(SECONDARY_POSITION)].lower()

                Player(name, gender, primaryp, secondaryp)
                Rank(name, ranking, confidence)


def calculate_ranks():
    cursor.execute("select name, id from players")
    all_results = cursor.fetchall()
    for result in all_results:
        id = result[1]
        cursor.execute("select weightedRank from ranks where playerid = %d" % id)
        all_ranks = cursor.fetchall()
        all_ranks = list((map(lambda x : x[0], all_ranks)))
        averageRank = sum(all_ranks) / len(all_ranks)
        cursor.execute("update players set rank = %d where id = %d" % (averageRank, id))


def get_sorted_ranks(f):
    f.write("name, gender, rank, primary, secondary\n")
    f.write("Beaters\n")
    output("beater", True, f)
    output("beater", False, f)

    f.write("Chasers\n")
    output("chaser", True, f)
    output("chaser", False, f)

    f.write("Keepers\n")
    output("keeper", True, f)
    output("keeper", False, f)

    f.write("Seekers\n")
    output("seeker", True, f)
    output("seeker", False, f)


def output(position, primary, f):
    if primary:
        f.write("primary\n")
        pos_type = 1
    else:
        f.write("secondary\n")
        pos_type = 2
    cursor.execute("select * from players where %s=%d order by rank desc" % (position, pos_type))
    results = cursor.fetchall()
    for result in results:
        f.write(format_player(result))
    f.write("")


def format_player(result):
    name = result[1]
    gender = result[2]
    positions = [result[3],result[4],result[5],result[6]]
    rank = result[7]
    types = ["beater", "chaser", "keeper", "seeker"]
    primary = "none"
    secondary = "none"
    if 1 in positions:
        primary = types[positions.index(1)]
    if 2 in positions:
        secondary = types[positions.index(2)]

    return "%s, %s, %d, %s, %s\n" % (name, gender, rank, primary, secondary)


def calculate_stats(f):
    get_stat_for_pos(f, "beater")
    get_stat_for_pos(f, "chaser")
    get_stat_for_pos(f, "keeper")
    get_stat_for_pos(f, "seeker")


def get_stat_for_pos(file, pos):
    cursor.execute(
        "select gender, %s, count(*), sum(rank), avg(rank), min(rank), max(rank) from players where %s > 0 group by gender, %s order by %s asc"
        % (pos, pos, pos, pos))
    results = cursor.fetchall()
    primaries = list(filter(lambda x: x[1] == 1, results))
    primary_count = float(sum(map(lambda x: x[2], primaries)))
    primary_average = sum(map(lambda x: x[3], primaries))/primary_count
    file.write("%d primary %ss, average %.3f\n" % (primary_count, pos, primary_average))
    for result in primaries:
        file.write("  %d %s, %.3f - %.3f - %.3f\n" % (result[2], result[0], float(result[5]), result[3]/result[2], float(result[6])))

    secondaries = list(filter(lambda x: x[1] == 2, results))
    secondary_count = float(sum(map(lambda x: x[2], secondaries)))
    secondary_average = sum(map(lambda x: x[3], secondaries)) / secondary_count
    file.write("%d secondary %ss, average %.3f\n" % (secondary_count, pos, secondary_average))
    for result in secondaries:
        file.write("  %d %s, %.3f - %.3f - %.3f\n" % (result[2], result[0], float(result[5]), result[3]/result[2], float(result[6])))
    file.write("\n")


if __name__ == "__main__":
    cursor.execute("delete from players")
    cursor.execute("delete from ranks")
    conn.commit()
    parse_input(CSV_PATHS)
    calculate_ranks()
    f = open("output.csv", "w+")
    get_sorted_ranks(f)
    f.close()
    f = open("stats.txt", "w+")
    calculate_stats(f)
    f.close()
    conn.commit()
    conn.close()
