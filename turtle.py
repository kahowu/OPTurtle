import math 
import pandas as pd
import numpy as np
import sys

PRECISION = 6
LONG = "long"
SHORT = "short"
NO_STRATEGY = "no_strategy"
TICK_SIZE = 0.000001


def get_PDC (curr_day, date_dict, df):
	idx = date_dict[curr_day]
	prev_idx = idx - 1
	curr_row = df.iloc[pd_idx]
	return row["Close"]

def get_high (curr_day, date_dict, df):
	idx = date_dict[curr_day]
	row = df.iloc[idx]
	return row["High"]

def get_low (curr_day, date_dict, df):
	idx = date_dict[curr_day]
	row = df.iloc[idx]
	return row["Low"]


def create_date_dict (dates):
	date_dict = dict()
	i = 0 
	size = len (dates)
	for i in range (0, size):
		date_dict[dates[i]] = i
	return date_dict


def true_range (curr_day, date_dict, df):
	curr_idx = date_dict[curr_day]
	prev_idx = curr_idx - 1
	prev_row = df.iloc[prev_idx]
	curr_row = df.iloc[curr_idx]
	curr_high = curr_row["High"]
	curr_low = curr_row["Low"]
	prev_close = prev_row["Close"]
	if curr_idx == 0:
		# Hack
		prev_close = curr_high
	tr = max (curr_high - curr_low, curr_high - prev_close, prev_close - curr_low)
	return tr 

def generate_tr_list (dates, date_dict, df):
	tr_list = []
	for d in dates:
		tr = true_range (d, date_dict, df)
		tr_list.append (tr)

	return tr_list

def calculate_n (PDN, TR): 
	# PDN: previous day's N
	# TR: current day's true range
	N =  (19 * PDN + TR) / 20 
	return N

# Start from day 2
def calculate_n_fixed (PDN, TR, idx):
	N =  (idx * PDN + TR) / (idx + 1)
	return N


def dollar_volatility (DPP, N):
	# DPP: dollars per point
	return N * DPP

# Volatility Adjusted Postion Units
def vadj_unit (equity, dv):
	one_percent = equity * 0.01
	unit = one_percent / dv
	return int(math.floor (unit))

def adj_trading_size (start, curr):
	loss = math.fabs (curr - start) / start
	if loss >= 0.1: 
		adj_size = start * 0.8
		return adj_size


# 20-day exponential moving average of the True Range.
# N represents the average range in price movement that
# a particular market makes in a single day, 
# accounting for opening gaps
def generate_n_list (tr_list, date_dict, df):
	n_list = []
	dates = df["Date"]
	for date in dates:
		curr_idx = date_dict[date]
		if curr_idx < 20: 
			if curr_idx == 0:
				n = tr_list[0]
				n_list.append(n)
			else:
				PDN = n_list[curr_idx - 1] 
				n = calculate_n_fixed (PDN, tr_list[curr_idx], curr_idx)
				n_list.append (n)

		else:
			PDN = n_list[curr_idx - 1] 
			n = calculate_n (PDN, tr_list[curr_idx])
			n_list.append (n)
	return n_list

# Generate a list of all breakouts 
def generate_bo_list (date_dict, dates, df): 
	bo_list = []
	for date in dates:
		curr_idx = date_dict[date]
		if curr_idx > 20: 
			high, low = prev_20 (date, date_dict, df)
			curr_row = df.iloc[curr_idx]
			curr_price = curr_row["Open"]
			if curr_price >= (high + TICK_SIZE):
				# Long  
				bo_list.append((date, curr_price, LONG))
			elif curr_price <= (low - TICK_SIZE):
				# Short 
				bo_list.append((date, curr_price, SHORT))

	return bo_list

# Find last breakout given a date
def find_last_breakout (curr_date, bo_list, date_dict, strategy_type):
	curr_idx = date_dict[curr_date] 
	last_bo = ()
	for bo in bo_list:
		bo_date = bo[0]
		bo_price = bo[1]
		bo_type = bo[2]
		bo_idx = date_dict[bo_date] 
		if (bo_idx < curr_idx) and (strategy_type == bo_type):
			last_bo = bo

	return last_bo

def is_loser_breakout (last_bo, date_dict, n_list, df):
	bo_date = last_bo[0]
	bo_price = last_bo[1]
	bo_type = last_bo[2]
	bo_idx = date_dict[bo_date]
	bo_N = n_list[bo_idx]

	if bo_type == LONG:
		# Check position before 10 day exit
		for i in range (1,10):
			curr_row = df.iloc[bo_idx + i]
			curr_price = curr_row["Close"]
			if ((bo_price  - (2 * bo_N)) >= curr_price):
				return True 
	else: 
		# Check position before 10 day exit
		for i in range (1,10):
			curr_row = df.iloc[bo_idx + i]
			curr_price = curr_row["Close"]
			if ((bo_price  + (2 * bo_N)) <= curr_price):
				return True
	
	return False



# Shorter-term system based on a 20-day breakout 
# If the last breakout was a loser, then entry signal -> 20-day breakout
# If the last breakout was a winner, then entry signal -> 55-day breakout
def sys_1_entry (curr_date, curr_N, curr_price, date_dict, df, bo_list, n_list):
	high, low = prev_20 (curr_date, date_dict, df)
	if curr_price >= (high + TICK_SIZE):
		print ("Initiate long position...")
		last_bo = find_last_breakout (curr_date, bo_list, date_dict, LONG)
		# Check to see if last breakout was a losing breakout
		if is_loser_breakout (last_bo, date_dict, n_list, df): 
			print ("Last breakout was a losing trade")
			print ("System 1: Buy one unit to initiate a long position")
		else:
			print ("Previous breakout was winner. Make 55-day breakout entry to avoid missing major moves")
			strategy_type = "long"
			sys_2_entry (curr_price, curr_date, date_dict, df) # Fail safe breakout point

		return LONG


	elif curr_price <= (low - TICK_SIZE):
		print ("Initiate short position...")
		last_bo = find_last_breakout (curr_date, bo_list, date_dict, SHORT)

		if is_loser_breakout (last_bo, date_dict, n_list, df):
			print ("Last breakout was a losing trade")
			print ("System 1: sell one unit to initiate a short position")
		else:
			print ("Previous breakout was winner. Make 55-day breakout entry to avoid missing major moves")
			strategy_type = "short"
			sys_2_entry (curr_price, curr_date, date_dict, df) # Fail safe breakout point
		return SHORT
	
	else:
		print ("No strategy")
		return NO_STRATEGY


# A simpler long-term system based on a 55-day breakout 
def sys_2_entry (curr_price, curr_date, date_dict, df):
	high, low = prev_55 (curr_date, date_dict, df)
	if curr_price >= (high + TICK_SIZE):
		print ("System 2: Buy one unit to initiate a long position")

	elif curr_price <= (low - TICK_SIZE):
		print ("System 2: Sell one unit to initiate a short position")

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


# All stops for the entire position would be placed at 2 N from the recently added unit 
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



def day_x_position (data, curr_date, length):
	duration = data[curr_day - length, curr_date]
	return min (duration), max (duration)


def sys_exit (curr_price, strategy_type, data, curr_date, length):
	if length == 10:
		min_price, max_price = day_x_position (data, curr_date, length)
	elif length == 20:
		min_price, max_price = day_x_position (data, curr_date, length)

	if strategy_type == LONG:
		if curr_price < min_price:
			print ("Exit for long position")

	elif strategy_type == SHORT:
		if curr_price < max_price:
			print ("Exit for short position")

# TO-DO: implement money win / loss ratio
def win_loss_ratio ():
	return

def update_entry (stop_list, first_gap, curr_idx):
	# print (first_gap, curr_idx)
	curr_stop = stop_list[curr_idx]
	for idx in range(first_gap, curr_idx): 
		stop_list[idx] = curr_stop

	return stop_list

# Get high-low previous 20 days
def prev_20 (curr_date, date_dict, df):
	idx = date_dict[curr_date]
	if idx > 20: 
		row = df.iloc[idx - 20: idx]
		date = row ["Date"]
		high = max(row ["Close"])
		low = min(row ["Close"])
	else:
		print "Not enough data for previous 20 days!"
	return high, low

# Get high-low previous 55 days
def prev_55 (curr_date, date_dict, df):
	idx = date_dict[curr_date]
	if idx > 55: 
		row = df.iloc[idx - 55: idx]
		date = row ["Date"]
		high = max(row ["Close"])
		low = min(row ["Close"])
	else:
		print "Not enough data for previous 55 days!"
	return high, low

