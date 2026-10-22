#!/usr/bin/env python3
"""october.py -- they said you can't script October.

A 2006 FOX playoff promo typed out a play-by-play, then crossed it out
when the real game went another way. Tagline: "You can't script October."
(Watch it: https://vimeo.com/45736773)

This generates OCTOBER, a screenplay in Fountain format about the World
Series of any year from 2000 on (the FOX era). For a finished Series it
types the real result before you see it, down to the date, the weekday,
the game number and the moon over the ballpark. For a Series that hasn't
happened yet, it writes every possible ending.

    python3 october.py --year 2004     # the Red Sox, the curse, the eclipse
    python3 october.py                 # this year: every possible ending
    python3 october.py --year 2016 --play
    python3 october.py --year 2019 -o october.fountain

Fountain is a plain-text screenplay format; the output opens in Highland,
Fade In, Slugline, Beat, WriterSolo, etc.
"""

import argparse
import datetime as dt
import math
import sys
import textwrap
import time

PROMO_URL = "https://vimeo.com/45736773"

# year: (champion, runner-up, runner-up's wins, date of the clinching game, notes)
# Checked against Wikipedia's World Series articles and Baseball-Reference.
WORLD_SERIES = {
    2000: ("New York Yankees", "New York Mets", 1, (10, 26), [
        "A Subway Series. The whole thing fits on one transit map."]),
    2001: ("Arizona Diamondbacks", "New York Yankees", 3, (11, 4), [
        "The first major-league games ever played in November."]),
    2002: ("Anaheim Angels", "San Francisco Giants", 3, (10, 27), [
        "The Rally Monkey is in the building. The monkey is undefeated.",
        "Percival to Bonds earlier in this Series? That one's going in a FOX promo."]),
    2003: ("Florida Marlins", "New York Yankees", 2, (10, 25), []),
    2004: ("Boston Red Sox", "St. Louis Cardinals", 0, (10, 27), [
        "Eighty-six years. Over.",
        "And look up. That's a total lunar eclipse."]),
    2005: ("Chicago White Sox", "Houston Astros", 0, (10, 26), [
        "Eighty-eight years for the South Side."]),
    2006: ("St. Louis Cardinals", "Detroit Tigers", 1, (10, 27), [
        "The same October FOX told everybody you can't script."]),
    2007: ("Boston Red Sox", "Colorado Rockies", 0, (10, 28), []),
    2008: ("Philadelphia Phillies", "Tampa Bay Rays", 1, (10, 29), [
        "Game 5 started Monday. Rain suspended it in the sixth. "
        "They finished it Wednesday. Still in the script."]),
    2009: ("New York Yankees", "Philadelphia Phillies", 2, (11, 4), []),
    2010: ("San Francisco Giants", "Texas Rangers", 1, (11, 1), []),
    2011: ("St. Louis Cardinals", "Texas Rangers", 3, (10, 28), []),
    2012: ("San Francisco Giants", "Detroit Tigers", 0, (10, 28), []),
    2013: ("Boston Red Sox", "St. Louis Cardinals", 2, (10, 30), []),
    2014: ("San Francisco Giants", "Kansas City Royals", 3, (10, 29), []),
    2015: ("Kansas City Royals", "New York Mets", 1, (11, 1), []),
    2016: ("Chicago Cubs", "Cleveland Indians", 3, (11, 2), [
        "One hundred and eight years.",
        "A rain delay before the tenth inning. Seventeen minutes. Scripted to the minute.",
        "It ends a little after midnight. Technically November 3rd."]),
    2017: ("Houston Astros", "Los Angeles Dodgers", 3, (11, 1), []),
    2018: ("Boston Red Sox", "Los Angeles Dodgers", 1, (10, 28), []),
    2019: ("Washington Nationals", "Houston Astros", 3, (10, 30), [
        "The road team won all seven games. Nobody won a single home game.",
        "Washington's first title."]),
    2020: ("Los Angeles Dodgers", "Tampa Bay Rays", 2, (10, 27), [
        "Every game at one neutral ballpark, Globe Life Field in Arlington, Texas."]),
    2021: ("Atlanta Braves", "Houston Astros", 2, (11, 2), []),
    2022: ("Houston Astros", "Philadelphia Phillies", 2, (11, 5), []),
    2023: ("Texas Rangers", "Arizona Diamondbacks", 1, (11, 1), [
        "The Rangers' first title. Ever."]),
    2024: ("Los Angeles Dodgers", "New York Yankees", 1, (10, 30), []),
    2025: ("Los Angeles Dodgers", "Toronto Blue Jays", 3, (11, 1), [
        "Game 3 went eighteen innings.",
        "And Game 7 goes to extra innings. It ends past midnight in Toronto."]),
}

FOX_ERA = 2000
PLAYOFF_TEAMS_PER_LEAGUE = 6  # the 12-team format, since 2022

UNIX_EPOCH_JD = 2440587.5
DELTA_T_DAYS = 70 / 86400  # Terrestrial Time runs ~70s ahead of UTC these days


def full_moon(k):
    """UTC time of full moon number `k` (k = n + 0.5), per Meeus, Astronomical Algorithms ch. 49."""
    T = k / 1236.85
    jde = (2451550.09766 + 29.530588861 * k + 0.00015437 * T**2
           - 0.000000150 * T**3 + 0.00000000073 * T**4)
    E = 1 - 0.002516 * T - 0.0000074 * T**2
    rad = math.radians
    M = rad(2.5534 + 29.10535670 * k - 0.0000014 * T**2 - 0.00000011 * T**3)
    Mp = rad(201.5643 + 385.81693528 * k + 0.0107582 * T**2 + 0.00001238 * T**3
             - 0.000000058 * T**4)
    F = rad(160.7108 + 390.67050284 * k - 0.0016118 * T**2 - 0.00000227 * T**3
            + 0.000000011 * T**4)
    om = rad(124.7746 - 1.56375588 * k + 0.0020672 * T**2 + 0.00000215 * T**3)
    jde += (-0.40614 * math.sin(Mp) + 0.17302 * E * math.sin(M)
            + 0.01614 * math.sin(2 * Mp) + 0.01043 * math.sin(2 * F)
            + 0.00734 * E * math.sin(Mp - M) - 0.00515 * E * math.sin(Mp + M)
            + 0.00209 * E * E * math.sin(2 * M) - 0.00111 * math.sin(Mp - 2 * F)
            - 0.00057 * math.sin(Mp + 2 * F) + 0.00056 * E * math.sin(2 * Mp + M)
            - 0.00042 * math.sin(3 * Mp) + 0.00042 * E * math.sin(M + 2 * F)
            + 0.00038 * E * math.sin(M - 2 * F) - 0.00024 * E * math.sin(2 * Mp - M)
            - 0.00017 * math.sin(om))
    days = jde - DELTA_T_DAYS - UNIX_EPOCH_JD
    return dt.datetime(1970, 1, 1, tzinfo=dt.timezone.utc) + dt.timedelta(days=days)


def full_moon_over(night):
    """True if the moon is full within 18 hours of a night game on `night` (first pitch ~8 PM Eastern)."""
    game = dt.datetime(night.year, night.month, night.day, tzinfo=dt.timezone.utc) + dt.timedelta(hours=24)
    k = round((night.year - 2000 + (night.timetuple().tm_yday - 1) / 365.25) * 12.3685 - 0.5) + 0.5
    return any(abs(full_moon(k + d) - game) < dt.timedelta(hours=18) for d in (-1, 0, 1))


def orderings(losses):
    """How many win/loss sequences end in a 4-`losses` series."""
    return math.comb(3 + losses, losses)


def series_paths():
    """Game-by-game ways a World Series can go, counting which league wins."""
    return 2 * sum(orderings(n) for n in range(4))


def slug_date(day):
    return f"{day:%A, %B} {day.day}, {day.year}".upper()


def build(year, today):
    s = []
    add = s.append

    add(f"Title: OCTOBER\nCredit: written by\nAuthor: a Python script\n"
        f"Source: inspired by the FOX promo that said it couldn't be done ({PROMO_URL})\n"
        f"Draft date: {today:%B %d, %Y}\n"
        f"Notes: The {year} World Series. Unofficial. Not affiliated with FOX or MLB.\n")

    add("FADE IN:")

    add("INT. A LIVING ROOM - OCTOBER 2006 - NIGHT")
    add("A TV glows. Between innings, a FOX playoff promo: a typewriter pecks out "
        "a play-by-play over the action. \"Percival delivers a 98 mph fastball to "
        "Bonds. Bonds lifts it to center. It should be caught fo--\" The real ball "
        "keeps going, and the typed line gets crossed out mid-word.")
    add("PROMO ANNOUNCER (V.O.)\nYou can't script October.")
    add("PATRUCK, on the couch, takes a chip. Chews. Doesn't argue. "
        "Lets FOX have it.")

    add(f"INT. GROUP CHAT - {today:%B %Y}".upper() + " - NIGHT")
    add(f"{today.year - 2006} years later. Little gray dots pulse.")
    add("THE BELIEVER\nRemember that FOX promo? \"You can't script October\"?")
    add("PATRUCK\nClassic.")
    add(f"THE BELIEVER\n{today.year - 2006} years, and you never once pushed back on that.")
    add("PATRUCK\n...Was I supposed to?")
    add("THE BELIEVER\nPick a year.")
    add(f"PATRUCK\n{year}.")

    if year in WORLD_SERIES:
        finished_series(add, year)
    else:
        unwritten_series(add, year, today)

    add("INT. A LIVING ROOM - OCTOBER 2006 - NIGHT")
    add("Back on the old TV, the same promo plays again. The typewriter. "
        "The crossed-out line.")
    add("PROMO ANNOUNCER (V.O.)\nYou can't script October.")
    add("THE SCRIPT\n(typing)\nI just did.")
    add(f"For the first time in {today.year - 2006} years, PATRUCK sets down the chip "
        f"and looks the TV in the eye.")
    add("PATRUCK\n(finally)\nYeah, you CAN script October.")

    add("> FADE OUT.")
    add("> THE END <")
    return "\n\n".join(s) + "\n"


def finished_series(add, year):
    champ, loser, losses, (month, day), notes = WORLD_SERIES[year]
    clinch = dt.date(year, month, day)
    game = 4 + losses
    record = f"4-{losses}"

    add("INT. A TYPEWRITER - CONTINUOUS")
    add("Keys clack. A page fills up before anyone has thrown a pitch.")
    add(f"THE SCRIPT\n(typing)\nThe {year} World Series. The {champ} beat the {loser}, "
        f"{record}. It ends in Game {game}, on a {clinch:%A}.")
    add("PATRUCK\n(mouth full)\nHuh.")
    if losses:
        add(f"THE SCRIPT\n(typing)\nA {record} series can go {orderings(losses)} different "
            f"ways, game by game. I picked the one that happened.")
    else:
        add("THE SCRIPT\n(typing)\nA sweep only goes one way. Four straight. "
            "Picking the right team was the hard part.")

    add(f"EXT. THE BALLPARK - {slug_date(clinch)} - NIGHT")
    action = f"World Series, Game {game}. The stands are a wall of noise."
    if clinch.month == 11:
        action += " It's November. October ran long. That was in the script too."
    if full_moon_over(clinch):
        action += " A full moon hangs over the upper deck, right where the math put it."
    add(action)

    add("INT. FOX BROADCAST BOOTH - CONTINUOUS")
    add("THE PLAY-BY-PLAY ANNOUNCER and THE COLOR ANALYST lean into their microphones. "
        "A FOX graphic reads WORLD SERIES.")
    add(f"PLAY-BY-PLAY ANNOUNCER\nThe {champ} are one out away.")
    shape = {
        0: "A sweep. Four games. That's not a script, that's a pamphlet.",
        1: "Five games. Efficient.",
        2: "Six games. Nobody's heart rate is normal.",
        3: "Game 7. The one everybody says you can't script.",
    }[losses]
    add(f"COLOR ANALYST\n{shape}")
    for note in notes:
        add(f"COLOR ANALYST\n{note}")
    add(f"PLAY-BY-PLAY ANNOUNCER\n(rising)\nAnd the {champ} are World Series champions!")

    add("INT. A LIVING ROOM - CONTINUOUS")
    add("PATRUCK stares at the TV, then at the typed page in THE BELIEVER's hand. "
        "Every line matches. Nothing is crossed out.")
    add("PATRUCK\nNot one line crossed out?")
    add("THE BELIEVER\nNot one.")


def unwritten_series(add, year, today):
    teams = PLAYOFF_TEAMS_PER_LEAGUE
    total = teams * teams * series_paths()

    add("INT. A TYPEWRITER - CONTINUOUS")
    add("Keys clack, then stop.")
    add(f"THE SCRIPT\nThe {year} World Series hasn't been played yet.")
    add("PATRUCK\n(shrugging)\nSo FOX wins this one?")
    add("THE SCRIPT\nI didn't say that.")

    if today.year == year and today.month == 10:
        add(f"INT. A TERMINAL WINDOW - {slug_date(today)} - RIGHT NOW")
        add("Green text crawls up a black screen. Someone has just run "
            "`python3 october.py`. The cursor blinks, thinking.")

    add("INT. A TYPEWRITER - MONTAGE")
    add("The keys go faster than keys should go. Pages fly.")
    add("THE SCRIPT\n(typing)\nAL champion in four. AL champion in five. "
        "NL champion in seven, after losing the first three...")
    add(f"THE SCRIPT\n(typing)\nSix playoff teams in each league. {teams * teams} possible "
        f"matchups. {series_paths()} ways each Series can go, game by game.")
    add(f"A stack of paper hits the desk: {total:,} versions of the {year} World Series.")
    add("THE SCRIPT\nWhichever one happens, I already wrote it.")
    add("PATRUCK\nIs that allowed?")
    add("THE BELIEVER\nThat's scripting.")


def perform(text, delay):
    """Print the screenplay like a typewriter, formatted for a terminal."""
    width = 72
    for block in text.split("\n\n"):
        lines = block.split("\n")
        head = lines[0]
        if head.startswith("Title:"):
            for line in lines:
                key, _, val = line.partition(": ")
                if key == "Title":
                    type_out(val.center(width), delay * 3)
                elif key in ("Credit", "Author"):
                    type_out(val.center(width), delay)
            print()
            continue
        if head.startswith("> "):
            out = head.strip("> <")
            type_out(out.rjust(width) if head.endswith(".") else out.center(width), delay)
        elif head.startswith(("EXT.", "INT.")) or head == "FADE IN:":
            type_out(head, delay)
        elif head.isupper() and len(lines) > 1:
            type_out(" " * 22 + head, delay)
            for line in lines[1:]:
                if line.startswith("("):
                    type_out(" " * 16 + line, delay)
                else:
                    for wrapped in textwrap.wrap(line, 36):
                        type_out(" " * 10 + wrapped, delay)
        else:
            for wrapped in textwrap.wrap(block, width):
                type_out(wrapped, delay)
        print()
        time.sleep(delay * 15)


def type_out(line, delay):
    for ch in line:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write("\n")


def main():
    today = dt.date.today()
    p = argparse.ArgumentParser(description="They said you can't script October.")
    p.add_argument("--year", type=int, default=today.year,
                   help=f"any World Series from {FOX_ERA} on (default: this year)")
    p.add_argument("--play", action="store_true", help="perform it in the terminal")
    p.add_argument("--speed", type=float, default=0.012, help="seconds per character with --play")
    p.add_argument("-o", "--out", help="write the Fountain screenplay to this file")
    args = p.parse_args()
    if args.year < FOX_ERA:
        p.error(f"pick a year from {FOX_ERA} on, when FOX started airing every World Series")

    script = build(args.year, today)
    if args.out:
        with open(args.out, "w") as f:
            f.write(script)
        scenes = sum(block.startswith(("INT.", "EXT.")) for block in script.split("\n\n"))
        print(f"Wrote {args.out}: OCTOBER, the {args.year} World Series, {scenes} scenes.")
    elif args.play:
        try:
            perform(script, args.speed)
        except KeyboardInterrupt:
            print("\n\nPATRUCK\n(from the couch)\nYou walked out? In October?")
    else:
        sys.stdout.write(script)


if __name__ == "__main__":
    main()
