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

import sys
import pandas as pd
from turtle import *

def setup (df): 
	dates = df["Date"]
	date_dict = create_date_dict (dates)
	tr_list = generate_tr_list (dates, date_dict, df)
	n_list = generate_n_list (tr_list,  date_dict, df)
	return tr_list, n_list, date_dict, dates

if __name__ == '__main__':
	arg = sys.argv
	# filename = arg[1]
	filename = "alibaba.csv"
	filedir = "./data/" + filename
	df = pd.read_csv(filedir)
	tr_list, n_list, date_dict, dates = setup(df)

	# # Pick a random date and then decide strategy
	curr_date = "15-05-07"

	print ("The chosen date is " + curr_date)

	print 
	print ("-------- Trade strategy --------")
	bo_list = generate_bo_list (date_dict, dates, df)
	curr_idx = date_dict[curr_date]
	curr_N = n_list[curr_idx]
	curr_row = df.iloc[curr_idx]
	curr_price = curr_row["Open"]
	decision = sys_1_entry (curr_date, curr_N, curr_price, date_dict, df, bo_list, n_list)
	equity = 1000000
	dv = dollar_volatility (curr_price, curr_N)
	unit_size = vadj_unit (equity, dv)
	print ("--------------------------------")
	print 

	print 
	print ("-------- Final decision --------")
	if (decision == LONG):
		print ("Given $ {}, buy one unit ({} shares) to initiate long position".format(equity, unit_size))
	elif (decision == SHORT):
		print ("Given $ {}, sell one unit ({} shares) to initiate short position".format(equity, unit_size))
	else:
		print ("No decision is made")
	print ("--------------------------------")

	print 
