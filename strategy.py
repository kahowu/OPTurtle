SYS_1_EXIT = 10
SYS_2_EXIT = 20
MAX_INVENTORY_SIZE = 4
SYS_1_ENTRY_RATIO = 0.5
SYS_1_ENTRY_RATIO = 0.5
MAX_SYS_1_ENTRIES = MAX_INVENTORY_SIZE * SYS_1_ENTRY_RATIO
MAX_SYS_2_ENTRIES = MAX_INVENTORY_SIZE * SYS_2_ENTRY_RATIO

class BreakoutEntry:
	def __init__(self, entry_price, entry_date, strategy_type, unit_size, stop_price=0):
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
		self.sys_1_entries = 0
		self.inv_size = MAX_INVENTORY_SIZE

	def add_unit (self, entry_obj):
		total_price = entry_obj.entry_price * entry_obj.unit_size
		new_equity = self.equity - total_price
		self.update_equity (new_equity)
		self.inventory.append (entry_obj)

	def remove_unit (self, entry_obj, exit_price):
		total_price = exit_price * entry_obj.unit_size
		new_equity = self.equity + total_price
		self.update_equity (new_equity)
		self.inventory.remove (entry_obj)

	def update_equity (self, new_equity):
		self.equity = new_equity

# Shorter-term system based on a 20-day breakout 
# If the last breakout was a loser, then entry signal -> 20-day breakout
# If the last breakout was a winner, then entry signal -> 55-day breakout
def sys_entry (portfolio, turtle, curr_date, curr_price, curr_N):
	if turtle.validate_date (curr_date, DAY_20):
		high, low = turtle.prev_20 (curr_date)

	unit_size = turtle.get_unit_size (curr_price, curr_N, portfolio)

	if curr_price >= (high + TICK_SIZE):
		print ("Initiate long position...")
		last_bo = turtle.find_last_breakout (curr_date, LONG)
		# Check to see if last breakout was a losing breakout
		if turtle.is_loser_breakout (last_bo): 
			print ("Last breakout was a losing trade")
			print ("System 1: Buy one unit to initiate a long position")
			while portfolio.sys_1_entries != MAX_SYS_1_ENTRIES:
				new_entry = BreakoutEntry (curr_price, curr_date, LONG, unit_size)
				portfolio.add_unit (new_entry)
			
		else:
			if turtle.validate_date (curr_date, DAY_55):
				print ("Previous breakout was winner. Make 55-day breakout entry to avoid missing major moves...")
				sys_2_entry (portfolio, turtle, curr_date, curr_price, unit_size) # Fail safe breakout point


	elif curr_price <= (low - TICK_SIZE):
		print ("Initiate short position...")
		last_bo = self.find_last_breakout (curr_date, SHORT)			
		if turtle.is_loser_breakout (last_bo):
			print ("Last breakout was a losing trade")
			print ("System 1: sell one unit to initiate a short position")
			while portfolio.sys_1_entries != MAX_SYS_1_ENTRIES:
				new_entry = BreakoutEntry (curr_price, curr_date, SHORT, unit_size)
				portfolio.add_unit (new_entry)
		else:
			if turtle.validate_date (curr_date, DAY_55):
				print ("Previous breakout was winner. Make 55-day breakout entry to avoid missing major moves...")
				sys_2_entry (portfolio, turtle, curr_date, curr_price, unit_size) # Fail safe breakout point

# A simpler long-term system based on a 55-day breakout 
def sys_2_entry (portfolio, turtle, curr_date, curr_price, unit_size):
	high, low = turtle.prev_55 (curr_date)
	if curr_price >= (high + TICK_SIZE):
		print ("System 2: Buy one unit to initiate a long position")
		while portfolio.sys_2_entries != MAX_SYS_2_ENTRIES:
			new_entry = BreakoutEntry (curr_price, curr_date, LONG, unit_size)
			portfolio.add_unit (new_entry)

	elif curr_price <= (low - TICK_SIZE):
		print ("System 2: Sell one unit to initiate a short position")
		while portfolio.sys_2_entries != MAX_SYS_2_ENTRIES:
			new_entry = BreakoutEntry (curr_price, curr_date, SHORT, unit_size)
			portfolio.add_unit (new_entry)

def create_strategy (turtle, equity):
	portfolio = Portfolio (equity)
	inventory = portfolio.inventory
	inv_size = portfolio.inv_size
	dates = turtle.dates
	last_trading_day = turtle.data_size
	curr_date = dates[0]
	# first date
	curr_idx = turtle.date_dict[curr_date]

	while curr_idx < last_trading_day:
		curr_N = n_list[curr_idx]
		curr_row = data.iloc[curr_idx]
		curr_price = curr_row["Open"]
		if inv_size != MAX_UNIT:
			sys_entry (portfolio, turtle, curr_date, curr_price, curr_N)
		else:
			# Check current price againt each item in the inventory
			for entry in inventory:
				if should_stop (entry, curr_price):
					portfolio.remove_unit (unit, curr_price)
					continue 

				if should_exit (entry, curr_price, curr_date, SYS_1_EXIT):
					portfolio.remove_unit (unit, curr_price)

		curr_idx += 1 


def should_exit (entry, curr_price, curr_date, exit_type):
	strategy_type = entry.strategy_type
	entry_price = entry.entry_price
	if sys_exit (exit_type, strategy_type, curr_price, curr_date, entry_price):
		print ("Should exit at current price")
		return True
	else:
		print ("Hold on to the entry for now")
		return False

def should_stop (entry, curr_price):
	strategy_type = entry.strategy_type
	if strategy_type == LONG:
		# If current price is lower or equal to stop price, stop
		return (entry.stop_price >= curr_price)
	elif strategy_type == SHORT
		# If current price is greater or equal to stop price, stop
		return (entry.stop_price <= curr_price)

def sys_exit (exit_type, strategy_type, curr_price, curr_date, entry_price):
	if strategy_type == LONG:
		if is_x_day_low (curr_price, curr_date, exit_type) and (curr_price > entry_price):
			print ("Exit for long position")
			return True

	elif strategy_type == SHORT:
		if is_x_day_high (curr_price, curr_date, exit_type) and (curr_price < entry_price)
			print ("Exit for short position")
			return True 

	return False



# Get high-low previous 10 days
def is_x_day_low (curr_price, curr_date, exit_type):
	date_dict = self.date_dict 
	curr_idx = date_dict[curr_date]
	data = self.data
	row = data.iloc[curr_idx - exit_type: idx] #
	lowest = min(row ["Close"])

	if curr_price < lowest:
		return True

	return False

def is_x_day_high (curr_price, curr_date, exit_type):
	date_dict = self.date_dict 
	curr_idx = date_dict[curr_date]
	data = self.data
	row = data.iloc[curr_idx - exit_type: idx] #
	highest = max(row ["Close"])

	if curr_price > highest:
		return True

	return False



