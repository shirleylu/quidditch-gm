import csv
import sqlite3
import math
from cmd import Cmd

class StdevFunc:
    def __init__(self):
        self.M = 0.0
        self.S = 0.0
        self.k = 1

    def step(self, value):
        if value is None:
            return
        tM = self.M
        self.M += (value - tM) / self.k
        self.S += (value - tM) * (value - self.M)
        self.k += 1

    def finalize(self):
        if self.k < 3:
            return None
        return math.sqrt(self.S / (self.k-2))


class Player:
    def __init__(self, name, gender, playing, team, primaryp, secondaryp):
        in_db = self.has_player(name)

        if not in_db:
            self.add_player(name, gender, playing, team, primaryp, secondaryp)

        # self.gender = gender
        # self.primaryP = primaryp
        # self.secondaryP = secondaryp

    def add_player(self, name, gender, playing, team, primaryp, secondaryp):
        beater = 0
        chaser = 0
        keeper = 0
        seeker = 0

        for p in secondaryp:
            if p == "beater":
                beater = 2
            elif p == "chaser":
                chaser = 2
            elif p == "keeper":
                keeper = 2
            elif p == "seeker":
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
            "insert into players (name, gender, length, team, beater, chaser, keeper, seeker) values ('%s','%s', %d, '%s', %d, %d, %d, %d)"
            % (name, gender, playing, team, beater, chaser, keeper, seeker))

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
                name = row[header.index(NAME)].lower()
                name.strip()
                gender = row[header.index(GENDER)].lower()
                playing = float(row[header.index(PLAYING)])
                team = row[header.index(TEAM)]

                # ranking = row[header.index(RANKING)]
                # confidence = row[header.index(CONFIDENCE)]

                primaryp = row[header.index(PRIMARY_POSITION)].lower()
                secondaryp = row[header.index(SECONDARY_POSITION)].lower().split(",")

                Player(name, gender, playing, team, primaryp, secondaryp)

                ranks = row[header.index(SECONDARY_POSITION) + 1:]
                # print(name)
                for i in range(3):
                    ranking = ranks[i*2]
                    confidence = ranks[i*2 + 1]
                    if not ranking:
                        continue
                    Rank(name, ranking, confidence)


def calculate_ranks():
    cursor.execute("select name, id from players")
    all_results = cursor.fetchall()
    for result in all_results:
        id = result[1]
        cursor.execute("select weightedRank from ranks where playerid = %d" % id)
        all_ranks = cursor.fetchall()
        all_ranks = list((map(lambda x : x[0], all_ranks)))
        average_rank = 0
        if len(all_ranks) > 0:
            average_rank = float(sum(all_ranks)) / len(all_ranks)
        cursor.execute("update players set rank = %0.3f where id = %d" % (average_rank, id))


def get_sorted_ranks(f):
    f.write("name, gender, rank, primary, secondary, years, team\n")
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
    years = result[3]
    team = result[4]
    positions = [result[5],result[6],result[7],result[8]]
    rank = result[9]
    types = ["beater", "chaser", "keeper", "seeker"]
    primary = "none"
    secondary = "none"
    if 1 in positions:
        primary = types[positions.index(1)]
    if 2 in positions:
        secondary = types[positions.index(2)]

    return "%s, %s, %.3f, %s, %s, %0.1f, %s\n" % (name, gender, rank, primary, secondary, years, team)


def calculate_stats(f):
    get_stat_for_pos(f, "beater")
    get_stat_for_pos(f, "chaser")
    get_stat_for_pos(f, "keeper")
    get_stat_for_pos(f, "seeker")


def get_stat_for_pos(file, pos):
    cursor.execute(
        "select gender, %s, count(*), sum(rank), avg(rank), min(rank), max(rank), stdev(rank) from players where %s > 0 group by gender, %s order by %s asc"
        % (pos, pos, pos, pos))
    results = cursor.fetchall()
    primaries = list(filter(lambda x: x[1] == 1, results))
    primary_count = float(sum(map(lambda x: x[2], primaries)))
    primary_average = sum(map(lambda x: x[3], primaries))/primary_count
    file.write("%d primary %ss, average %.3f\n" % (primary_count, pos, primary_average))
    for result in primaries:
        stdev = -1
        if result[7]:
            stdev = float(result[7])
        file.write("  %d %s, %.3f - %.3f - %.3f, %.3f" % (result[2], result[0], float(result[5]), result[3]/result[2], float(result[6]), stdev))

        if stdev >= 0:
            cursor.execute("select count(*) from players where rank > %f and %s = 1 and gender = '%s'" % (result[4] + stdev, pos, result[0]))
            count = cursor.fetchone()
            file.write(", %d elites\n" % count[0])
        else:
            file.write("\n")

    secondaries = list(filter(lambda x: x[1] == 2, results))
    secondary_count = float(sum(map(lambda x: x[2], secondaries)))
    secondary_average = sum(map(lambda x: x[3], secondaries)) / secondary_count
    file.write("%d secondary %ss, average %.3f\n" % (secondary_count, pos, secondary_average))
    for result in secondaries:
        stdev = -1
        if result[7]:
            stdev = float(result[7])
        file.write("  %d %s, %.3f - %.3f - %.3f, %.3f\n" % (result[2], result[0], float(result[5]), result[3]/result[2], float(result[6]), stdev))
    file.write("\n")

def show(draft, gender, position, limit):
    if gender.lower() == "all":
        gender = "gender not null"
    elif gender.lower() == "non-male":
        gender = "gender != 'male'"
    else:
        gender = "gender='%s'" % gender

    if draft.lower() == "all":
        draft = "(drafted is null or drafted is not null)"
    elif draft.lower() == "undrafted":
        draft = "drafted is null"

    if position.upper() == "all":
        cursor.execute("select * from players where %s and %s order by rank desc limit %d" % (gender, draft, limit))
    else:
        cursor.execute("select * from players where %s > 0 and %s and %s order by %s asc, rank desc limit %d" % (position, gender, draft, position, limit))

    types = ["beater", "chaser", "keeper", "seeker"]
    for result in cursor.fetchall():
        name = result[1]
        gender = result[2][0]
        positions = result[5:9]
        p = types[positions.index(1)]
        rank = result[9]
        print("(%d) %s [%s] [%s] - %.3f - %s" % (result[0], name, gender, p, rank, result[10]))

def show_all_undrafted():
    cursor.execute("select id, name, gender, rank from players where keeper=1 and drafted is null order by rank desc")
    results = cursor.fetchall();
    keepers = []
    for result in results:
        keepers.append("(%s) %s [%s] [%0.3f]" % (result[0], result[1][:16], result[2][0], float(result[3])))

    cursor.execute("select id, name, gender, rank from players where chaser=1 and drafted is null order by rank desc")
    results = cursor.fetchall();
    chasers = []
    for result in results:
        chasers.append("(%s) %s [%s] [%0.3f]" % (result[0], result[1][:16], result[2][0], float(result[3])))

    cursor.execute("select id, name, gender, rank from players where beater=1 and drafted is null order by rank desc")
    results = cursor.fetchall();
    beaters = []
    for result in results:
        beaters.append("(%s) %s [%s] [%0.3f]" % (result[0], result[1][:16], result[2][0], float(result[3])))

    cursor.execute("select id, name, gender, rank from players where seeker=1 and drafted is null order by rank desc")
    results = cursor.fetchall();
    seekers = []
    for result in results:
        seekers.append("(%s) %s [%s] [%0.3f]" % (result[0], result[1][:16], result[2][0], float(result[3])))

    print("keepers\tchasers\tbeaters\tseekers".expandtabs(40))
    for i in range (max([len(keepers), len(chasers), len(beaters), len(seekers)])):
        k = "\t"
        c = "\t"
        b = "\t"
        s = "\t"
        if i < len(keepers):
            k = keepers[i] + "\t"
        if i < len(chasers):
            c = chasers[i] + "\t"
        if i < len(beaters):
            b = beaters[i] + "\t"
        if i < len(seekers):
            s = seekers[i] + "\t"

        print(("%s%s%s%s" % (k,c,b,s)).expandtabs(40))

def draft(name):
    cursor.execute("select name from players where name='%s'" % name)
    result = cursor.fetchone()
    print("drafting %s" % result[0])
    cursor.execute("update players set drafted = 'AUSTIN' where name = '%s'" % name)
    conn.commit()

def track(name, team):
    cursor.execute("select id, name from players where name='%s'" % name)
    result = cursor.fetchone()
    print("tracking (%s) %s to %s" % (result[0], result[1], team.strip()))
    cursor.execute("update players set drafted = '%s' where id = %s" % (team.strip(), result[0]))
    conn.commit()

def teams():
    cursor.execute("select name, gender, rank, keeper, chaser, beater, seeker, drafted from players order by drafted asc, rank desc")
    players = cursor.fetchall()
    types = ["keeper", "chaser", "beater", "seeker"]
    teams = {}
    team_names = []
    max_players = 0
    for player in players:
        team = player[7]
        if not team:
            team = "undrafted"
            continue
        positions = player[3:7]
        pos = types[positions.index(1)]
        if not team in team_names:
            team_names.append(team)
            teams[team] = {'keeper':[], 'chaser':[], 'beater':[], 'seeker':[], 'total': 0, 'all':[]}
        teams[team][pos].append({'name': player[0], 'gender': player[1][0], 'rank': float(player[2])})
        teams[team]['all'].append({'name': player[0], 'gender': player[1][0], 'rank': float(player[2]), 'position': pos})
        teams[team]['total'] += 1
        if teams[team]['total'] > max_players:
            max_players = teams[team]['total']

    string = ""
    for team in team_names:
        string += team + "\t"
    print(string.expandtabs(40))

    string = ""
    for team in team_names:
        team_players = teams[team]
        ratings = list(map(lambda x: float(x['rank']), team_players["keeper"]))
        rating = sum(ratings)
        string += "%d keepers (%0.3f)" % (len(team_players["keeper"]), rating) + "\t"
    print(string.expandtabs(40))

    string = ""
    for team in team_names:
        team_players = teams[team]
        rating = sum(list(map(lambda x: x['rank'], team_players["chaser"])))
        string += "%d chasers (%0.3f)" % (len(team_players["chaser"]), rating) + "\t"
    print(string.expandtabs(40))

    string = ""
    for team in team_names:
        team_players = teams[team]
        rating = sum(list(map(lambda x: x['rank'], team_players["beater"])))
        string += "%d beaters (%0.3f)" % (len(team_players["beater"]), rating) + "\t"
    print(string.expandtabs(40))

    string = ""
    for team in team_names:
        team_players = teams[team]
        rating = sum(list(map(lambda x: x['rank'], team_players["seeker"])))
        string += "%d seekers (%0.3f)" % (len(team_players["seeker"]), rating) + "\t"
    print(string.expandtabs(40))

    for i in range(max_players):
        string = ""
        for team in team_names:
            if i < len(teams[team]['all']):
                p = teams[team]['all'][i]
                string += "[%s][%s] %s, %0.3f\t" % (p['position'][0], p['gender'][0], p['name'], p['rank'])
            else:
                string += "\t"
        print(string.expandtabs(40))

        # k_sum = sum(map(lambda x: x['rank'], team_players["keeper"]))
        # ks = list(map(lambda x: "%s [%s] [%0.3f]" % (x['name'], x['gender'], x['rank']), team_players["keeper"]))
        #
        # c_total = len(team_players["chaser"])
        # c_sum = sum(map(lambda x: x['rank'], team_players["chaser"]))
        # cs = list(map(lambda x: "%s [%s] [%0.3f]" % (x['name'], x['gender'], x['rank']), team_players["chaser"]))
        #
        # b_total = len(team_players["beater"])
        # b_sum = sum(map(lambda x: x['rank'], team_players["beater"]))
        # bs = list(map(lambda x: "%s [%s] [%0.3f]" % (x['name'], x['gender'], x['rank']), team_players["beater"]))
        #
        # s_total = len(team_players["seeker"])
        # s_sum = sum(map(lambda x: x['rank'], team_players["seeker"]))
        # ss = list(map(lambda x: "%s [%s] [%0.3f]" % (x['name'], x['gender'], x['rank']), team_players["seeker"]))
        #
        # print("%d keepers")


conn = sqlite3.connect('west.db')
conn.create_aggregate("stdev", 1, StdevFunc)
cursor = conn.cursor()

PLAYERS = {}
CSV_PATHS = ["./west.csv"]

RANKING = "Ranking"
CONFIDENCE = "Confidence"
# FIRST_NAME = "Name (First)"
# LAST_NAME = "Name (Last)"
PLAYING = "How long have you been playing?"
TEAM = "Team"
NAME = "Name"
GENDER = "Gender"
PRIMARY_POSITION = "Primary Position"
SECONDARY_POSITION = "Secondary Position"

class Prompt(Cmd):

    def do_setup(self, args):
        """standard setup"""
        cursor.execute("delete from players")
        cursor.execute("delete from ranks")
        parse_input(CSV_PATHS)
        calculate_ranks()
        conn.commit()

    def do_output(self, args):
        """output players by rank and stats"""
        f = open("output.csv", "w+")
        get_sorted_ranks(f)
        f.close()
        f = open("stats.txt", "w+")
        calculate_stats(f)
        f.close()

    def do_resetdraft(self, args):
        """resets all players to undrafted"""
        cursor.execute("update players set drafted=NULL")
        conn.commit()

    def do_show(self, args):
        """shows all players for a position. show [drafted] [gender] [type] [limit]"""
        args = args.split(" ")
        if len(args) < 3 or len(args) > 4:
            print("show [drafted] [gender] [type] [limit]")
            print("drafted: all, undrafted")
            print("gender: all, male, female, non-binary, non-male")
            print("type: all, beater, chaser, keeper, seeker")
            print("limit: <a number>")
            return

        draft = args[0]
        gender = args[1]
        position = args[2]
        limit = 1000
        if len(args) == 4:
            limit = int(args[3])

        show(draft, gender, position, limit)

    def do_undrafted(self, args):
        '''show all undrafted players by position'''
        show_all_undrafted()

    def do_draft(self, args):
        '''draft someone onto Austin/Shirley'''
        if len(args) == 0:
            print("draft [name]")
            return
        draft(args)

    def do_track(self, args):
        '''track a draft'''
        args = args.split(",")
        if len(args) != 2:
            print("track [name],[team]")
            return
        track(args[0], args[1])

    def do_teams(self, args):
        '''output teams and positional strengths'''
        teams()

    def do_quit(self, args):
        """Quits"""
        print("Quitting.")
        conn.close()
        raise SystemExit

    def do_exit(self, args):
        """Quits"""
        print("Quitting.")
        conn.close()
        raise SystemExit

if __name__ == "__main__":
    prompt = Prompt()
    prompt.prompt ="> "
    prompt.cmdloop('Starting prompt...')
