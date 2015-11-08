from constants import *

# All stops for the entire position would be placed at 2 N from the recently added unit 
def stop_strategy_1 (entries, N, gap_flag, strategy_type):
	# 2 percent risk 
	half_N = N / 2
	two_N = N * 2 
	stop_list = []
	size = len (entries)
	prev = 0
	first_gap = 0

	if strategy_type == LONG:
		if gap_flag == False:
			max_price = max(entries)
			stop = max_price - two_N
			stop_list = [round(stop, PRECISION)] * len (entries)
		else:
			for i in range (0, size):
				stop = round((entries[i] - two_N), PRECISION)
				stop_list.append(stop)
				if i == 0: 
					# First unit 
					first_gap = 0 
				elif round ((entries[i] - prev), PRECISION) != half_N:
					# Adjust the price just before gap entry
					adj_price = entries[i - 1] + half_N
					adj_stop = round ((adj_price - two_N), PRECISION)
					stop_list[i - 1] = adj_stop 
					stop_list = self.update_entry (stop_list, first_gap, i - 1)

					# There has to be a gap 
					first_gap = i 

				stop_list = self.update_entry (stop_list, first_gap, i)
				prev = entries[i]


	elif strategy_type == SHORT:
		if gap_flag == False:
			max_price = max(entries)
			stop = max_price + two_N
			stop_list = [round(stop, PRECISION)] * len (entries)
		else:
			for i in range (0, size):
				# print(first_gap)
				stop = round((entries[i] + two_N), PRECISION)
				stop_list.append(stop)
				if i == 0: 
					# First unit 
					first_gap = 0 
				elif round ((prev - entries[i]), PRECISION) != half_N:
					# Adjust the price just before gap entry
					adj_price = entries[i - 1] - half_N
					adj_stop = round ((adj_price + two_N), PRECISION)
					stop_list[i - 1] = adj_stop 
					stop_list = self.update_entry (stop_list, first_gap, i - 1)

					# There has to be a gap 
					first_gap = i 

				stop_list = self.update_entry (stop_list, first_gap, i)
				prev = entries[i]

	return stop_list

# Higher profitability, but lower win/loss ratio. AKA The whipsaw
def stop_strategy_2 (entries, N, strategy_type):
	half_N = float(N / 2) 
	stop_list = []
	size = len (entries)
	if strategy_type == LONG:
		for i in range (0, size):
			stop_list.append (round ((entries[i] - half_N), PRECISION))


	elif strategy_type == SHORT:
		for i in range (0, size):	
			stop_list.append (round ((entries[i] + half_N), PRECISION))

	return stop_list