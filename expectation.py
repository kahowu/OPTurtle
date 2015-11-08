
# Expected gain per trade
# IT IS NOT ABOUT THE FREQUENCY OF HOW CORRECT YOU ARE
# BUT THE MAGNITUDE
def expected_return (winning_percentage, average_winner, losing_percentage, average_loser):
	return (winning_percentage * average_winner) - (losing_percentage * average_loser)