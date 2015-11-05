def true_range (curr_high, curr_low, PDC):
	return max (curr_high - curr_low, curr_high - PDC, PDC - curr_low)

# 20-dat exponential moving average of the True Range.
# N represents the average range in price movement that
# a particular market makes in a single day, 
# accoutning for opening gaps
def n_def (PDN, TR):
	# PDN: previous day's N
	# TR: current day's true range 
	return (19 * PDN + TR) / 20 



