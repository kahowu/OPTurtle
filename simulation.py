from opturtle import *
from strategy import *

EQUITY = 1000000

if __name__ == '__main__':
	data = read_data (sys.argv)
	turtle = OPTurtle (data)
	turtle.setup()
	create_strategy (turtle, EQUITY)