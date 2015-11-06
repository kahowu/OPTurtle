
if __name__ == '__main__':
	arg = sys.argv
	filename = arg[1]
	filedir = "./data/" + filename
	df = pd.read_csv(filedir)