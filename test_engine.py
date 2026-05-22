from engine import (
    calc_group_match_points,
    calc_group_ranking_points,
    calc_knockout_points,
    calc_champion_points
)

print("GROUP MATCH TESTS")
print(calc_group_match_points("A", "A"))        # 3
print(calc_group_match_points("DRAW", "DRAW"))  # 4
print(calc_group_match_points("A", "B"))        # 0

print("\nGROUP RANKING TESTS")
print(calc_group_ranking_points(
    ["Brazil", "Spain", "Japan", "Morocco"],
    ["Brazil", "Germany", "Japan", "Spain"]
))  # 2

print(calc_group_ranking_points(
    ["Brazil", "Spain", "Japan", "Morocco"],
    ["Brazil", "Spain", "Japan", "Morocco"]
))  # 3

print(calc_group_ranking_points(
    ["Brazil", "Spain", "Japan", "Morocco"],
    ["Germany", "France", "Argentina", "Brazil"]
))  # 0

print("\nCHAMPION TESTS")
print(calc_champion_points("Argentina", "Argentina"))  # 10
print(calc_champion_points("Argentina", "France"))     # 0

print("\nKNOCKOUT TESTS")
print(calc_knockout_points("Argentina", "NORMAL", "Argentina", "NORMAL"))  # 3
print(calc_knockout_points("Argentina", "ET", "Argentina", "ET"))          # 4
print(calc_knockout_points("Argentina", "PEN", "Argentina", "PEN"))        # 5

print(calc_knockout_points("Argentina", "PEN", "Argentina", "NORMAL"))     # 2
print(calc_knockout_points("Argentina", "NORMAL", "Argentina", "PEN"))     # 2
print(calc_knockout_points("Argentina", "ET", "Argentina", "PEN"))         # 2

print(calc_knockout_points("Argentina", "ET", "France", "ET"))             # 1
print(calc_knockout_points("Argentina", "PEN", "France", "PEN"))           # 2
print(calc_knockout_points("Argentina", "NORMAL", "France", "NORMAL"))     # 0

print(calc_knockout_points("Argentina", "NORMAL", "France", "ET"))         # 0
print(calc_knockout_points("Argentina", "ET", "France", "PEN"))            # 0