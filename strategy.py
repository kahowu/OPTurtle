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

from __future__ import division
from opturtle_v1 import *
from constants import *
import matplotlib.pyplot as plt


# Shorter-term system based on a 20-day breakout 
# If the last breakout was a loser, then entry signal -> 20-day breakout
# If the last breakout was a winner, then entry signal -> 55-day breakout
def sys_entry (portfolio, turtle, curr_date, curr_price, curr_N):
	half_N = np.divide (curr_N, 2)
	unit_size = turtle.get_unit_size (curr_price, curr_N, portfolio)
	breakout_price = curr_price
	long_stop_price = curr_price - half_N
	short_stop_price = curr_price + half_N
	added_entry = False

	if turtle.validate_date (curr_date, DAY_20):
		highest, lowest = turtle.prev_20 (curr_date)
	else:
		# print ("Not enough days to do analysis!")
		return added_entry

	if curr_price > (highest + TICK_SIZE):
		# print ("Initiate long position...")
		# Check to see if last breakout was a losing breakout
		if turtle.is_last_breakout_loser (curr_date):
			# print ("Last breakout was a losing trade")
			# print ("System 1: Buy to initiate a long position")
			while portfolio.sys_1_entries != MAX_SYS_1_ENTRIES:
				breakout_price = round(breakout_price, PRECISION)
				stop_price = round(long_stop_price, PRECISION)
				new_entry = BreakoutEntry (breakout_price, stop_price, curr_date, SYS_1_LONG, unit_size)
				print_entry (new_entry)
				portfolio.add_unit (new_entry)
				added_entry = True
				# stop_price = breakout_price
				# breakout_price += half_N
			
		else:
			if turtle.validate_date (curr_date, DAY_55):
				# print ("Previous breakout was winner. Make 55-day breakout entry to avoid missing major moves...")
				added_entry = sys_2_entry (portfolio, turtle, curr_date, curr_price, half_N, unit_size) # Fail safe breakout point

	elif curr_price < (lowest - TICK_SIZE):
		# print ("Initiate short position...")
		if turtle.is_last_breakout_loser (curr_date):
			# print ("Last breakout was a losing trade")
			# print ("System 1: Sell to initiate a short position")
			while portfolio.sys_1_entries != MAX_SYS_1_ENTRIES:
				breakout_price = round(breakout_price, PRECISION)
				stop_price = round(short_stop_price, PRECISION)
				new_entry = BreakoutEntry (breakout_price, stop_price, curr_date, SYS_1_SHORT, unit_size)
				print_entry (new_entry)
				portfolio.add_unit (new_entry)
				added_entry = True
				# stop_price = breakout_price
				# breakout_price -= half_N
		else:
			if turtle.validate_date (curr_date, DAY_55):
				# print ("Previous breakout was winner. Make 55-day breakout entry to avoid missing major moves...")
				added_entry = sys_2_entry (portfolio, turtle, curr_date, curr_price, half_N, unit_size) # Fail safe breakout point

	return added_entry

# A simpler long-term system based on a 55-day breakout 
def sys_2_entry (portfolio, turtle, curr_date, curr_price, half_N, unit_size):
	breakout_price = curr_price
	long_stop_price = curr_price - half_N
	short_stop_price = curr_price + half_N
	highest, lowest = turtle.prev_55 (curr_date)
	added_entry = False

	if curr_price > (highest + TICK_SIZE):
		# print ("System 2: Buy one unit to initiate a long position")
		while portfolio.sys_2_entries != MAX_SYS_2_ENTRIES:
			breakout_price = round(breakout_price, PRECISION)
			stop_price = round(long_stop_price, PRECISION)
			new_entry = BreakoutEntry (breakout_price, stop_price, curr_date, SYS_2_LONG, unit_size)
			print_entry (new_entry)
			portfolio.add_unit (new_entry)
			added_entry = True
			# stop_price = breakout_price
			# breakout_price += half_N

	elif curr_price < (lowest - TICK_SIZE):
		# print ("System 2: Sell one unit to initiate a short position")
		while portfolio.sys_2_entries != MAX_SYS_2_ENTRIES:
			breakout_price = round(breakout_price, PRECISION)
			stop_price = round(short_stop_price, PRECISION)
			new_entry = BreakoutEntry (breakout_price, stop_price, curr_date, SYS_2_SHORT, unit_size)
			print_entry (new_entry)
			portfolio.add_unit (new_entry)
			added_entry = True
			# stop_price = breakout_price
			# breakout_price -= half_N

	return added_entry


def create_strategy (turtle, equity):
	print "The starting equity is " + str(equity)
	portfolio = Portfolio (equity)
	inventory = portfolio.inventory
	dates = turtle.dates
	n_list = turtle.n_list
	data = turtle.data
	last_trading_day = turtle.data_size

	curr_idx = 0
	unit_size_list = [] 
	equity_list = []
	price_list = []

	while curr_idx < last_trading_day:
		added_entry = False
		curr_N = n_list[curr_idx]
		curr_row = data.iloc[curr_idx]
		curr_price = curr_row["Open"]
		curr_date = dates[curr_idx]
		unit_size = turtle.get_unit_size (curr_price, curr_N, portfolio)
		unit_size_list.append(unit_size)
		price_list.append (curr_price)
		print (curr_date, curr_price)
		if len(inventory) != MAX_INVENTORY_SIZE:
			added_entry = sys_entry (portfolio, turtle, curr_date, curr_price, curr_N)
			print added_entry
			if added_entry:
				print "Entry"
			equity_list.append (portfolio.equity)
			
		# Check current price againt each item in the inventory
		# if not added_entry:
		for entry in list(inventory):
			if turtle.should_stop (entry, curr_price):
				print "Stop"
				print_entry (entry)
				portfolio.remove_unit (entry, curr_price)
				continue 

			if turtle.should_exit (entry, curr_price, curr_date, SYS_2_EXIT):
				print "Exit"
				print_entry (entry)
				portfolio.remove_unit (entry, curr_price)

			equity_list.append (portfolio.equity)

		curr_idx += 1 

		# Naive implementation: evaluate whether we should increase or decrease equity percentage traded
		if not inventory:
			current_equity = portfolio.equity
			notional_equity = portfolio.notional_equity 
			print current_equity, notional_equity
			balance = (current_equity - notional_equity) / notional_equity 
			curr_percentage = turtle.equity_percentage
			# if balance < 0:
			# 	balance = balance / 2
			new_percentage = curr_percentage + balance
			if new_percentage < 0.01:
				turtle.equity_percentage = 0.01
			else:
				turtle.equity_percentage = min (new_percentage, 0.20)
			print turtle.equity_percentage
			portfolio.notional_equity = current_equity

	for entry in list(inventory):
		portfolio.remove_unit(entry, curr_price)

	print "Clear out inventory at the end of available trading days"
	print "The final equity is " + str(portfolio.equity)
	percentage_return = (portfolio.equity - equity) / equity
	print "The percentage return is " + str(percentage_return * 100) 


def print_entry (entry):
	print "entry: {0}, stop: {1}, date: {2}, type: {3}, unit size: {4}".format(entry.entry_price, entry.stop_price, entry.entry_date, entry.strategy_type, entry.unit_size)
