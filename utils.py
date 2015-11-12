import matplotlib.pyplot as plt
def plot (data):
	limit = len (data) 
	plt.plot(range(0, limit), data["Close"])
	plt.xlabel('Day')
	plt.ylabel('Price')	
	plt.show()



# def buy_short ():

# 	short_pos = (entry_price - curr_price) * unit_size + entry_price * unit_size =  (2 * entry_price - curr_price ) * unit_size
# 	long_pos = (curr_price - entry_price) * unit_size + entry_price * unit_size = curr_price * unit_size
