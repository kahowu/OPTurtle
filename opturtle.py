# Copyright (c) 2015 
# Author: Xerxes Wu
# Permission to use, copy, modify, and distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

import math 
import pandas as pd
import numpy as np
import sys

PRECISION = 2
LONG = "long"
SHORT = "short"
NO_STRATEGY = "no_strategy"
TICK_SIZE = 0.01
MAX_UNIT = 4
DAY_20_BREAKOUT = "20"
DAY_55_BREAKOUT = "55"
NOT_ENOUGH_DATA = -1 
NONE = "none"
DAY_20 = 20
DAY_55 = 55
DAY_10_EXIT = 10

class OPTurtle:
	def __init__ (self, data):
		self.data = data 
		self.tr_list = []
		self.n_list = [] 
		self.bo_list = []
		self.date_dict = dict()
		self.dates = []
		self.data_size = len (data)

	def setup (self):
		self.create_date_dict ()
		self.generate_tr_list ()
		self.generate_n_list ()
		self.generate_bo_list ()

	def create_date_dict (self):
		data = self.data
		dates = data["Date"]
		date_dict = dict()
		i = 0 
		size = len (dates)
		for i in range (0, size):
			date_dict[dates[i]] = i

		self.date_dict = date_dict
		self.dates = dates

	def true_range (self, curr_day):
		data = self.data
		curr_idx = self.date_dict[curr_day]
		prev_idx = curr_idx - 1
		prev_row = data.iloc[prev_idx]
		curr_row = data.iloc[curr_idx]
		curr_high = curr_row["High"]
		curr_low = curr_row["Low"]
		prev_close = prev_row["Close"]
		if curr_idx == 0:
			prev_close = curr_high
		tr = max (curr_high - curr_low, curr_high - prev_close, prev_close - curr_low)
		return round(tr, PRECISION) 

	# 20-day exponential moving average of the True Range.
	# N represents the average range in price movement that
	# a particular market makes in a single day, 
	# accounting for opening gaps
	def calculate_n (self, PDN, TR): 
		N =  (19 * PDN + TR) / 20 
		return round(N, PRECISION)


	# Used to generate N when there is not current day is less than 21
	def calculate_n_first_20 (self, PDN, TR, idx):
		N =  (idx * PDN + TR) / (idx + 1)
		return round(N, PRECISION)


	# DPP: dollars per point
	def dollar_volatility (self, DPP, N):
		return round(N * DPP, PRECISION)


	# Volatility Adjusted Position Units
	def vadj_unit (self, equity, dv):
		one_percent = equity * 0.01
		unit = one_percent / dv
		return int(math.floor (unit))

	# Generate list of Ns
	def generate_n_list (self):
		tr_list = self.tr_list
		date_dict = self.date_dict
		dates = self.dates
		n_list = []
		for date in dates:
			curr_idx = date_dict[date]
			if curr_idx < DAY_20: 
				if curr_idx == 0:
					n = tr_list[0]
					n_list.append(n)
				else:
					PDN = n_list[curr_idx - 1] 
					n = self.calculate_n_first_20 (PDN, tr_list[curr_idx], curr_idx)
					n_list.append (n)

			else:
				PDN = n_list[curr_idx - 1] 
				n = self.calculate_n (PDN, tr_list[curr_idx])
				n_list.append (n)
		
		self.n_list = n_list

	# Generate a list of all true range 
	def generate_tr_list (self):
		tr_list = []
		for d in self.dates:
			tr = self.true_range (d)
			tr_list.append (tr)

		self.tr_list = tr_list

	# Generate a list of all breakouts 
	def generate_bo_list (self): 
		dates = self.dates
		date_dict = self.date_dict
		data = self.data

		bo_list = []
		for date in dates:
			curr_idx = date_dict[date]
			if curr_idx >= DAY_20: 
				high, low = self.prev_20 (date)
				curr_row = data.iloc[curr_idx]
				curr_price = curr_row["Open"]
				if curr_price >= (high + TICK_SIZE):
					# Long  
					bo_list.append((date, curr_price, LONG))
				elif curr_price <= (low - TICK_SIZE):
					# Short 
					bo_list.append((date, curr_price, SHORT))


		self.bo_list = bo_list

	# Find last breakout given a date
	def find_last_breakout (self, curr_date, strategy_type):
		date_dict = self.date_dict
		bo_list = self.bo_list
		curr_idx = date_dict[curr_date] 
		last_bo = None
		for bo in bo_list:
			bo_date = bo[0]
			bo_price = bo[1]
			bo_type = bo[2]
			bo_idx = date_dict[bo_date] 
			if (bo_idx < curr_idx) and (strategy_type == bo_type):
				last_bo = bo
		return last_bo

	# Check if the last breakout is a winning trade 
	def is_loser_breakout (self, last_bo):
		if last_bo is None:
			print "No breakout yet"
			return True

		date_dict = self.date_dict
		n_list = self.n_list
		data = self.data

		bo_date = last_bo[0]
		bo_price = last_bo[1]
		bo_type = last_bo[2]
		bo_idx = date_dict[bo_date]
		bo_N = n_list[bo_idx]

		if bo_type == LONG:
			# Check position before 10 day exit
			for i in range (1, DAY_10_EXIT):
				if (bo_idx + i) < self.data_size:
					curr_row = data.iloc[bo_idx + i]
					curr_price = curr_row["Close"]
					if np.subtract (bo_price, (2 * bo_N)) >= curr_price:
						return True 
				else:
					break
		else: 
			# Check position before 10 day exit
			for i in range (1,DAY_10_EXIT):
				if (bo_idx + i) < self.data_size:
					curr_row = data.iloc[bo_idx + i]
					curr_price = curr_row["Close"]
					if np.add (bo_price, (2 * bo_N)) <= curr_price:
						return True
				else:
					break
			
		return False

	# Get high-low for previous 20 days
	def prev_20 (self, curr_date):
		date_dict = self.date_dict
		idx = date_dict[curr_date]
		data = self.data 
		if idx >= 20: 
			row = data.iloc[idx - 20: idx]
			date = row ["Date"]
			high = max(row ["Close"])
			low = min(row ["Close"])
			return high, low
		else:
			print "Not enough data for previous 20 days!"


	# Get high-low for previous 55 days
	def prev_55 (self, curr_date):
		date_dict = self.date_dict
		idx = date_dict[curr_date]
		data = self.data 
		if idx >= 55: 
			row = data.iloc[idx - 55: idx]
			date = row ["Date"]
			high = max(row ["Close"])
			low = min(row ["Close"])
			return high, low
		else:
			print "Not enough data for previous 55 days!"

	def validate_date (self, curr_date, day_type):
		date_dict = self.date_dict
		idx = date_dict[curr_date]
		if idx < day_type: 
			return False

		return True

	# Shorter-term system based on a 20-day breakout 
	# If the last breakout was a loser, then entry signal -> 20-day breakout
	# If the last breakout was a winner, then entry signal -> 55-day breakout
	def sys_1_entry (self, curr_date, curr_price):
		if self.validate_date (curr_date, DAY_20):
			high, low = self.prev_20 (curr_date)
		else:
			print ("No strategy")
			return NO_STRATEGY, NONE

		if curr_price >= (high + TICK_SIZE):
			print ("Initiate long position...")
			last_bo = self.find_last_breakout (curr_date, LONG)
			# Check to see if last breakout was a losing breakout
			if self.is_loser_breakout (last_bo): 
				print ("Last breakout was a losing trade")
				print ("System 1: Buy one unit to initiate a long position")
				return LONG, DAY_20_BREAKOUT
			else:
				if self.validate_date (curr_date, DAY_55):
					print ("Previous breakout was winner. Make 55-day breakout entry to avoid missing major moves...")
					self.sys_2_entry (curr_date, curr_price) # Fail safe breakout point
					return LONG, DAY_55_BREAKOUT
				else:
					print ("No strategy")
					return NO_STRATEGY, NONE



		elif curr_price <= (low - TICK_SIZE):
			print ("Initiate short position...")
			last_bo = self.find_last_breakout (curr_date, SHORT)			
			if self.is_loser_breakout (last_bo):
				print ("Last breakout was a losing trade")
				print ("System 1: sell one unit to initiate a short position")
				return SHORT, DAY_20_BREAKOUT
			else:
				if self.validate_date (curr_date, DAY_55):
					print ("Previous breakout was winner. Make 55-day breakout entry to avoid missing major moves...")
					self.sys_2_entry (curr_date, curr_price) # Fail safe breakout point
					return SHORT, DAY_55_BREAKOUT
				else:
					print ("No strategy")
					return NO_STRATEGY, NONE
		
		else:
			print ("No strategy")
			return NO_STRATEGY, NONE


	# A simpler long-term system based on a 55-day breakout 
	def sys_2_entry (self, curr_date, curr_price):
		high, low = self.prev_55 (curr_date)
		if curr_price >= (high + TICK_SIZE):
			print ("System 2: Buy one unit to initiate a long position")

		elif curr_price <= (low - TICK_SIZE):
			print ("System 2: Sell one unit to initiate a short position")

	# Add trading units at breakout price
	def adding_units (self, breakout_price, N, gap_flag):
		entries = []
		curr_price = breakout_price
		half_N = np.divide (N, 2)
		
		if gap_flag == False:
			for i in range (0, MAX_UNIT):
				if i == 0: 
					entries.append(round(curr_price, PRECISION))
				else: 
					curr_price = np.add (curr_price, half_N)
					entries.append(round(curr_price, PRECISION))

			return entries

	# Higher profitability, but lower win/loss ratio. AKA The whipsaw
	def stop_strategy_2 (self, entries, N, strategy_type):
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

	def suggest_strategy (self, curr_date, equity):

		date_dict = self.date_dict
		data = self.data
		n_list = self.n_list

		if date_dict[curr_date] < 21:
			return "Not enough data"

		unit_list = []
		stop_list = [] 


		curr_idx = date_dict[curr_date]
		curr_N = n_list[curr_idx]
		curr_row = data.iloc[curr_idx]
		curr_price = curr_row["Open"]

		print 
		print ("-------- Trade strategy --------")
		position, breakout_type = self.sys_1_entry(curr_date, curr_price)
		dv = self.dollar_volatility (curr_price, curr_N)
		unit_size = self.vadj_unit (equity, dv)
		print ("--------------------------------")
		print

		print
		print ("-------- Final decision --------")
		if (position != NO_STRATEGY):
			unit_list = self.adding_units (curr_price, curr_N, False)
			stop_list = self.stop_strategy_2 (unit_list, curr_N, position)
			print unit_list
			print stop_list
			print ("Given $ {}, buy {} turtle units ({} shares) to initiate {} position with {}-day breakout".format(equity, MAX_UNIT, unit_size * MAX_UNIT
				, position, breakout_type))
		else:
			print ("No decision is made")
		print ("-------- Final decision --------")
		print


def read_data (arg):
	filename = arg[1]
	filedir = "./data/" + filename
	data = pd.read_csv(filedir)
	return data
