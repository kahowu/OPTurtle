import matplotlib.pyplot as plt
def plot (data):
	limit = len (data) 
	plt.plot(range(0, limit), data["Close"])
	plt.xlabel('Day')
	plt.ylabel('Price')	
	plt.show()