import math 
import pandas as pd
import numpy as np
import sys

PRECISION = 6
LONG = "long"
SHORT = "short"


def get_PDC (data):


def true_range (curr_high, curr_low, PDC):
	tr = max (curr_high - curr_low, curr_high - PDC, PDC - curr_low)
	return tr 

# 20-day exponential moving average of the True Range.
# N represents the average range in price movement that
# a particular market makes in a single day, 
# accounting for opening gaps
def n_def (PDN, TR):
	# PDN: previous day's N
	# TR: current day's true range
	N =  (19 * PDN + TR) / 20 
	return N

def dollar_volatility (DPP, N):
	# DPP: dollars per point
	dv = N * DPP
	return dv 

# Volatility Adjusted Postion Units
def vadj_unit (equity, dv, N):
	one_percent = equity * 0.01
	unit = one_percent / (N * dv) 
	return math.floor (unit) 

def adj_trading_size (start, curr):
	loss = math.fabs (curr - start) / start
	if loss >= 0.1: 
		adj_size = start * 0.8
		return adj_size

# Shorter-term system based on a 20-day breakout 
# If the last breakout was a loser, then entry signal -> 20-day breakout
# If the last breakout was a winner, then entry signal -> 55-day breakout
def sys_1_entry (curr, data, tick_size, last_breakout, N, last_breakout_type, next_price):
	high, low = prev_20 (data)
	if curr >= (high + tick_size):
		# Check to see if last breakout was a losing breakout
		if ((last_breakout - (2 * N)) >= next_price) and (last_breakout_type == type_long):
			print ("Last breakout was a losing trade")
			print ("Buy one unit to initiate a long position")
		else:
			print ("Previous trade was winner. Make 55-day breakout entry to avoid missing major moves")
			strategy_type = "long"
			sys_2_entry (curr, data) # Fail safe breakout point


	elif curr <= (low - tick_size):
		if ((last_breakout + (2 * N)) <= next_price) and (last_breakout_type == type_short):
			print ("Last breakout was a losing trade")
			print ("Sell one unit to initiate a short position")
		else:
			print ("Previous trade was winner. Make 55-day breakout entry to avoid missing major moves")
			strategy_type = "short"
			sys_2_entry (curr, data) # Fail safe breakout point


# A simpler long-term system based on a 55-day breakout 
def sys_2_entry (curr, data):
	high, low = prev_55 (data)
	if curr >= (high + tick_size):
		print ("Buy one unit to initiate a long position")

	elif curr <= (low - tick_size):
		print ("Sell one unit to initiate a short position")

def adding_units (breakout_entry, N, max_unit, gap_flag):
	entries = []
	curr = breakout_entry
	half_N = N / 2 
	if gap_flag == False:
		for i in range (0, max_unit):
			if i == 0: 
				entries.append(curr)
			else: 
				curr += half_N
				entries.append(curr)

		return entries


# All stops for the entire position would be palced at 2 N from the recently added unit 
def stop_strategy_1 (entries, N, gap_flag, strategy_type):
	# 2 percent risk 
	half_N = float(N / 2) 
	two_N = N * 2 
	stop_list = []
	size = len (entries)
	prev = 0
	first_gap = 0

	if strategy_type == LONG:
		if gap_flag == False:
			max_price = max(entries)
			stop = max_price - two_N
			stop_list = [stop] * len (entries)
		else:
			for i in range (0, size):
				# print(first_gap)
				stop = entries[i] - two_N
				stop_list.append(stop)
				if i == 0: 
					# First unit 
					first_gap = 0 
				elif round ((entries[i] - prev), PRECISION) != half_N:
					# Adjust the price just before gap entry
					adj_price = entries[i - 1] + half_N
					adj_stop = round ((adj_price - two_N), PRECISION)
					stop_list[i - 1] = adj_stop 
					stop_list = update_entry (stop_list, first_gap, i - 1)

					# There has to be a gap 
					first_gap = i 

				stop_list = update_entry (stop_list, first_gap, i)
				prev = entries[i]


	elif strategy_type == SHORT:
		if gap_flag == False:
			max_price = max(entries)
			stop = max_price + two_N
			stop_list = [stop] * len (entries)
		else:
			for i in range (0, size):
				# print(first_gap)
				stop = entries[i] + two_N
				stop_list.append(stop)
				if i == 0: 
					# First unit 
					first_gap = 0 
				elif round ((prev - entries[i]), PRECISION) != half_N:
					# Adjust the price just before gap entry
					adj_price = entries[i - 1] - half_N
					adj_stop = round ((adj_price + two_N), PRECISION)
					stop_list[i - 1] = adj_stop 
					stop_list = update_entry (stop_list, first_gap, i - 1)

					# There has to be a gap 
					first_gap = i 

				stop_list = update_entry (stop_list, first_gap, i)
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



def day_10_position (data, curr_date, length):
	duration = data[curr_day - length, curr_date]
	return min (duration), max (duration)


def sys_exit (curr_price, strategy_type, data, curr_date, length):
	if length == 10:
		min_price, max_price = day_10_position (data, curr_date)
	elif length == 20:
		min_price, max_price = day_20_position (data, curr_date)

	if strategy_type == LONG:
		if curr_price < min_price:
			print ("Exit for long position")

	elif strategy_type == SHORT:
		if curr_price < max_price:
			print ("Exit for short position")


def win_loss_ratio ():
	return

def update_entry (stop_list, first_gap, curr_idx):
	# print (first_gap, curr_idx)
	curr_stop = stop_list[curr_idx]
	for idx in range(first_gap, curr_idx): 
		stop_list[idx] = curr_stop

	return stop_list

# TO-DO: write function according to dataset
def prev_20 (data):
	high = 0
	low = 0 
	return high, low

# TO-DO: write function according to dataset
def prev_55 (data):
	high = 0
	low = 0 
	return high, low

if __name__ == '__main__':
	long_entries = [28.30, 28.90, 29.50, 30.10]
	# short_entries = list(reversed(long_entries))
	# print short_entries
	# stop_list = stop_strategy_1(short_entries, 1.2, False, SHORT)
	stop_list = stop_strategy_2 (long_entries, 1.2, LONG)
	print stop_list
	# arg = sys.argv
	# filename = arg[1]
	# filedir = "./data/" + filename
	# df = pd.read_csv(filedir)

