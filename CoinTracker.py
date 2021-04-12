import matplotlib.pyplot as plt

class CoinTracker():
	def __init__(self):
		self.memorial = ReadData("pennies_collection")
		self.wheat = ReadData("wheat_collection")

	def addPenny(self, year, mark):
		if not year.isdigit():
			return "Invalid Year"

		if mark == "": mark = "None"
		if int(year) < 100:
			year = "%d" % (int(year) + 1900)

		if 1909 <= int(year) <= 1958:
			self.wheat[year][mark] += 1
		elif 1959 <= int(year) <= 1981:
			self.memorial[year][mark] += 1
		else:
			return "Invalid Year"

		return "sall good"

	def saveData(self):
		SaveData(self.memorial, "pennies_collection")
		SaveData(self.wheat, "wheat_collection")
		return "sall good"

def ReadData(filename):
	ret_data = {}
	if ".csv" not in filename:
		filename += ".csv"	

	data = []
	with open("data/%s" % filename, 'r') as f:
		data = f.readlines()
	data = [x.replace("\n", "") for x in data[1:]]
	for d in data:
		splitted = d.split(',')
		year = splitted[0]
		if "VDB" in year: year = year[:4]
		philly = int(splitted[1])
		denver = int(splitted[2])
		sanfran = int(splitted[3])
		if year in ret_data:
			ret_data[year]["None"] += philly
			ret_data[year]["D"] += denver
			ret_data[year]["S"] += sanfran
		else:
			ret_data[year] = {"None": philly, "D": denver, "S": sanfran}

	return ret_data

def SaveData(data, filename):
	years = sorted(data.keys())
	with open("data/%s.csv" % filename, "w") as f:
		f.write("Year,No Mint Mark,D,S\n")
		for y in years:
			f.write("%s,%d,%d,%d\n" % (y, data[y]["None"], data[y]["D"], data[y]["S"]))

def GetData():
	memorial = ReadData("pennies_collection")
	memorial_supply = ReadData("pennies_supply")
	wheat = ReadData("wheat_collection")
	wheat_supply = ReadData("wheat_supply")

	return memorial, memorial_supply, wheat, wheat_supply

def PlotData(coll, supply, fig=None):
	
	coll_totals = []
	coll_D_totals = []
	supply_totals = []
	short_years = []
	for year in coll:
		tot = coll[year]["None"] + coll[year]["D"] + coll[year]["S"]
		coll_totals.append(tot)
		coll_D_totals.append(coll[year]["D"])

		tot = (supply[year]["None"] + supply[year]["D"] + supply[year]["S"]) / 1e8
		supply_totals.append(tot)

		short_years.append(int(year)-1900)

	#tot_overall = sum(coll_totals)
	#thirds = [0,0]
	#for i in range(len(coll_totals)):
			
	#	if thirds[0] == 0 and sum(coll_totals[:i+1]) >= (tot_overall / 3):
	#		thirds[0] = i-1
	#	if thirds[0] != 0 and sum(coll_totals[thirds[0]:i+1]) >= (tot_overall / 3):
	#		thirds[1] = i-1
	#		break
	#thirds = [short_years[x] for x in thirds]

	if fig == None:
		fig, ax = plt.subplots()
	else:
		ax = fig.add_subplot(2,1,2)

	fig.set_size_inches(10, 4)

	ax.bar(short_years, coll_totals)
	ax.bar(short_years, coll_D_totals)
	ax.legend(["All","D"])
	if 81 in short_years:
		plt.axvline(x=69.5, color="black", linestyle="--", linewidth=0.7)
		plt.axvline(x=76.5, color="black", linestyle="--", linewidth=0.7)
		plt.text(64, ax.get_ylim()[1]*0.95, sum(coll_totals[:11]))
		plt.text(73, ax.get_ylim()[1]*0.95, sum(coll_totals[11:18]))
		plt.text(79, ax.get_ylim()[1]*0.95, sum(coll_totals[18:]))
	plt.xticks(rotation=-45)
	ax.set_xticks(short_years)
	ax.set_xticklabels(["'%d" % y for y in short_years])

	ax2 = ax.twinx()
	ax2.plot(short_years, supply_totals, color="red")
	ax2.set_ylim([0, ax2.get_ylim()[1]])
	
	return fig

def GetPlots():
	memorial, mem_supply, wheat, wheat_supply = GetData()
	count = [memorial[y]["None"] + memorial[y]["D"] + memorial[y]["S"] for y in memorial]
	fig = PlotData(memorial, mem_supply)
	fig.suptitle("%d Memorial Pennies (1959-1981)" % sum(count))
	fig.tight_layout()	

	count = [wheat[y]["None"] + wheat[y]["D"] + wheat[y]["S"] for y in wheat]
	fig2 = PlotData(wheat, wheat_supply)
	fig2.suptitle("%d Wheat Pennies (1909-1958)" % sum(count))
	fig2.tight_layout()

	return fig, fig2
