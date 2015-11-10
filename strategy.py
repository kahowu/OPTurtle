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

from opturtle_v1 import *
from constants import *

# Shorter-term system based on a 20-day breakout 
# If the last breakout was a loser, then entry signal -> 20-day breakout
# If the last breakout was a winner, then entry signal -> 55-day breakout
def sys_entry (portfolio, turtle, curr_date, curr_price, curr_N, exit_type):
	half_N = np.divide (curr_N, 2)
	unit_size = turtle.get_unit_size (curr_price, curr_N, portfolio)
	breakout_price = curr_price
	stop_price = curr_price - half_N

	if turtle.validate_date (curr_date, DAY_20):
		highest, lowest = turtle.prev_20 (curr_date)
	else:
		# print ("Not enough days to do analysis!")
		return

	if curr_price > (highest + TICK_SIZE):
		# print ("Initiate long position...")
		# Check to see if last breakout was a losing breakout
		if turtle.is_last_breakout_loser (curr_date):
			# print ("Last breakout was a losing trade")
			# print ("System 1: Buy to initiate a long position")
			while portfolio.sys_1_entries != MAX_SYS_1_ENTRIES:
				breakout_price = round(breakout_price, PRECISION)
				stop_price = round(stop_price, PRECISION)
				new_entry = BreakoutEntry (breakout_price, stop_price, curr_date, SYS_1_LONG, unit_size)
				print_entry (new_entry)
				portfolio.add_unit (new_entry)
				stop_price = breakout_price
				breakout_price += half_N
			
		else:
			if turtle.validate_date (curr_date, DAY_55):
				# print ("Previous breakout was winner. Make 55-day breakout entry to avoid missing major moves...")
				sys_2_entry (portfolio, turtle, curr_date, curr_price, half_N, unit_size) # Fail safe breakout point
			else:
				# print ("Not enough days to do perform system 2 entry!")
				return

	elif curr_price < (lowest - TICK_SIZE):
		# print ("Initiate short position...")
		if turtle.is_last_breakout_loser (curr_date):
			# print ("Last breakout was a losing trade")
			# print ("System 1: Sell to initiate a short position")
			while portfolio.sys_1_entries != MAX_SYS_1_ENTRIES:
				breakout_price = round(breakout_price, PRECISION)
				stop_price = round(stop_price, PRECISION)
				new_entry = BreakoutEntry (breakout_price, stop_price, curr_date, SYS_1_SHORT, unit_size)
				print_entry (new_entry)
				portfolio.add_unit (new_entry)
				stop_price = breakout_price
				breakout_price -= half_N
		else:
			if turtle.validate_date (curr_date, DAY_55):
				# print ("Previous breakout was winner. Make 55-day breakout entry to avoid missing major moves...")
				sys_2_entry (portfolio, turtle, curr_date, curr_price, half_N, unit_size) # Fail safe breakout point
			else:
				# print ("Not enough days to do perform system 2 entry!")
				return

# A simpler long-term system based on a 55-day breakout 
def sys_2_entry (portfolio, turtle, curr_date, curr_price, half_N, unit_size):
	breakout_price = curr_price
	stop_price = curr_price - half_N
	highest, lowest = turtle.prev_55 (curr_date)

	if curr_price > (highest + TICK_SIZE):
		# print ("System 2: Buy one unit to initiate a long position")
		while portfolio.sys_2_entries != MAX_SYS_2_ENTRIES:
			breakout_price = round(breakout_price, PRECISION)
			stop_price = round(stop_price, PRECISION)
			new_entry = BreakoutEntry (breakout_price, stop_price, curr_date, SYS_2_LONG, unit_size)
			print_entry (new_entry)
			portfolio.add_unit (new_entry)
			stop_price = breakout_price
			breakout_price += half_N

	elif curr_price < (lowest - TICK_SIZE):
		# print ("System 2: Sell one unit to initiate a short position")
		while portfolio.sys_2_entries != MAX_SYS_2_ENTRIES:
			breakout_price = round(breakout_price, PRECISION)
			stop_price = round(stop_price, PRECISION)
			new_entry = BreakoutEntry (breakout_price, stop_price, curr_date, SYS_2_SHORT, unit_size)
			print_entry (new_entry)
			portfolio.add_unit (new_entry)
			stop_price = breakout_price
			breakout_price -= half_N

def create_strategy (turtle, equity):
	print "The starting equity is " + str(equity)
	portfolio = Portfolio (equity)
	inventory = portfolio.inventory
	dates = turtle.dates
	n_list = turtle.n_list
	data = turtle.data
	last_trading_day = turtle.data_size

	curr_idx = 0


	while curr_idx < last_trading_day:
		curr_N = n_list[curr_idx]
		curr_row = data.iloc[curr_idx]
		curr_price = curr_row["Open"]
		curr_date = dates[curr_idx]
		if len(inventory) != MAX_INVENTORY_SIZE:
			sys_entry (portfolio, turtle, curr_date, curr_price, curr_N, SYS_1_EXIT)
		else:
			# Check current price againt each item in the inventory
			for entry in inventory:
				if turtle.should_stop (entry, curr_price):
					print_entry (entry)
					portfolio.remove_unit (entry, curr_price)
					continue 

				if turtle.should_exit (entry, curr_price, curr_date, SYS_1_EXIT):
					print_entry (entry)
					portfolio.remove_unit (entry, curr_price)

		curr_idx += 1 

	while inventory != []:
		portfolio.remove_unit(inventory[0], curr_price)

	print "The final equity is " + str(portfolio.equity)
	percentage_return = (portfolio.equity - equity) / equity
	print "The percentage return is " + str(percentage_return * 100) 


def print_entry (entry):
	print "entry: {0}, stop: {1}, date: {2}, type: {3}, unit size: {4}".format(entry.entry_price, entry.stop_price, entry.entry_date, entry.strategy_type, entry.unit_size)
