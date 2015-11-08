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
from stop import *
from constants import *

class BreakoutEntry:
	def __init__(self, entry_price, stop_price, entry_date, strategy_type, unit_size):
		self.entry_price = entry_price
		self.stop_price = stop_price
		self.strategy_type = strategy_type
		self.entry_date = entry_date
		self.unit_size = unit_size

class Portfolio:
	def __init__(self, equity):
		self.equity = equity
		self.inventory = []
		self.sys_1_entries = 0 
		self.sys_2_entries = 0
		self.inv_size = MAX_INVENTORY_SIZE

	def add_unit (self, entry_obj):
		if (entry_obj.strategy_type == SYS_1_LONG) or (entry_obj.strategy_type == SYS_1_SHORT):
			self.sys_1_entries += 1
		else:
			self.sys_2_entries += 1

		total_price = entry_obj.entry_price * entry_obj.unit_size
		new_equity = round((self.equity - total_price), PRECISION)
		self.update_equity (new_equity)
		self.inventory.append (entry_obj)


	def remove_unit (self, entry_obj, exit_price):
		if (entry_obj.strategy_type == SYS_1_LONG) or (entry_obj.strategy_type == SYS_1_SHORT):
			self.sys_1_entries -= 1
		else:
			self.sys_2_entries -= 1

		total_price = exit_price * entry_obj.unit_size
		new_equity = round((self.equity + total_price), PRECISION)
		self.update_equity (new_equity)
		self.inventory.remove (entry_obj)

	def update_equity (self, new_equity):
		self.equity = new_equity

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

	def get_unit_size (self, curr_price, curr_N, portfolio):
		dv = self.dollar_volatility (curr_price, curr_N)
		unit_size = self.vadj_unit (portfolio.equity, dv)
		return unit_size

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
			# print "No breakout yet"
			return True

		date_dict = self.date_dict
		n_list = self.n_list
		data = self.data

		bo_date = last_bo[0]
		bo_price = last_bo[1]
		bo_type = last_bo[2]
		bo_idx = date_dict[bo_date]
		bo_N = n_list[bo_idx]
		limit = self.data_size - bo_idx

		if bo_type == LONG:
			# Check position before 10 day exit
			for i in range (1, DAY_20_EXIT):
				if (bo_idx + i) < self.data_size:
					curr_row = data.iloc[bo_idx + i]
					curr_price = curr_row["Close"]
					if np.subtract (bo_price, (2 * bo_N)) >= curr_price:
						return True 
				else:
					break
		else: 
			# Check position before 10 day exit
			for i in range (1, DAY_20_EXIT):
				if (bo_idx + i) < self.data_size:
					curr_row = data.iloc[bo_idx + i]
					curr_price = curr_row["Close"]
					if np.add (bo_price, (2 * bo_N)) <= curr_price:
						return True
				else:
					break


			
		return False

	# Check if the curent price is lower than previous 20 days
	def is_x_day_low (self, curr_price, curr_date, exit_type):
		date_dict = self.date_dict 
		data = self.data
		curr_idx = date_dict[curr_date]
		row = data.iloc[curr_idx - exit_type: curr_idx] #
		lowest = min(row ["Close"])
		if curr_price < lowest:
			return True
		return False

	# Check if the curent price is higher than previous 20 days
	def is_x_day_high (self, curr_price, curr_date, exit_type):
		date_dict = self.date_dict 
		data = self.data
		curr_idx = date_dict[curr_date]
		row = data.iloc[curr_idx - exit_type: curr_idx] #
		highest = max(row ["Close"])
		if curr_price > highest:
			return True
		return False

	# Get high-low for previous 20 days
	def prev_20 (self, curr_date):
		date_dict = self.date_dict
		idx = date_dict[curr_date]
		data = self.data 
		if idx >= 20: 
			row = data.iloc[idx - 20: idx]
			highest = max(row ["Close"])
			lowest = min(row ["Close"])
			return highest, lowest
		else:
			print "Not enough data for previous 20 days!"


	# Get high-low for previous 55 days
	def prev_55 (self, curr_date):
		date_dict = self.date_dict
		idx = date_dict[curr_date]
		data = self.data 
		if idx >= 55: 
			row = data.iloc[idx - 55: idx]
			highest = max(row ["Close"])
			lowest = min(row ["Close"])
			return highest, lowest
		else:
			print "Not enough data for previous 55 days!"

	def validate_date (self, curr_date, day_type):
		date_dict = self.date_dict
		idx = date_dict[curr_date]
		if idx < day_type: 
			return False

		return True

	def should_exit (self, entry, curr_price, curr_date, exit_type):
		strategy_type = entry.strategy_type
		entry_price = entry.entry_price

		if (strategy_type == SYS_1_LONG) or (strategy_type == SYS_2_LONG):
			if self.is_x_day_low (curr_price, curr_date, exit_type) and (curr_price > entry_price):
				# print ("Exit for long position")
				return True

		elif (strategy_type == SYS_1_SHORT) or (strategy_type == SYS_2_SHORT):
			if self.is_x_day_high (curr_price, curr_date, exit_type) and (curr_price < entry_price):
				# print ("Exit for short position")
				return True 
	
		return False

	def should_stop (self, entry, curr_price):
		strategy_type = entry.strategy_type
		if strategy_type == LONG:
			# If current price is lower or equal to stop price, stop
			return (entry.stop_price >= curr_price)
		elif strategy_type == SHORT:
			# If current price is greater or equal to stop price, stop
			return (entry.stop_price <= curr_price)


def read_data (arg):
	filename = arg[1]
	filedir = "./data/" + filename
	data = pd.read_csv(filedir)
	return data
