import matplotlib.pyplot as plt
import time
import requests
import json

def GetCopperPrice():
	url = "https://api.metals.live/v1/spot/copper"
	
	try:
		resp = requests.get(url)
		json_data = resp.json()
		return float(json_data[-1]["price"])
	except:
		return 0

class CoinTracker():
	def __init__(self):
		self.memorial = ReadData("pennies_collection")
		self.wheat = ReadData("wheat_collection")
		self.last_year = ("", "")
		self.history = []

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

		self.last_year = (year, mark)
		self.history.append((year, mark))

		return "sall good"

	def getHistory(self):
		hist = ""
		for coin in self.history:
			temp = coin[0]
			if coin[1] != "None": temp += " %s" % coin[1]
			temp += "\n"
			hist = temp + hist
		return hist


	def saveData(self):
		try:
			SaveData(self.memorial, "pennies_collection")
		except Exception as ex:
			print("Failed to save memorial penny data")
			print(ex)
			return ex

		try:
			SaveData(self.wheat, "wheat_collection")
			self.history = []
		except Exception as ex:
			print("Failed to save wheat penny data")
			print(ex)
			return ex

		return "sall good"

	def revertPrevState(self):
		rem = ""
		if self.history: #self.last_year[0] != "":
			last = self.history.pop()
			year = last[0] #self.last_year[0]
			mark = last[1] #self.last_year[1]
			if 1909 <= int(year) <= 1958:
				self.wheat[year][mark] -= 1
			elif 1959 <= int(year) <= 1981:
				self.memorial[year][mark] -= 1
			rem = "Removed %s" % year
			if mark != "None": rem += " %s" % mark
			#self.last_year = ("", "")
			return rem
		else:
			return "Nothing to undo"

	def getPlots(self):
		mem_supply = ReadData("pennies_supply")
		wheat_supply = ReadData("wheat_supply")
		fig = PlotData(self.memorial, mem_supply, "Memorial Cents (1959-1981)")
		#fig.suptitle("%d Memorial Pennies (1959-1981)" % sum(count))
		#fig.tight_layout()	

		#count = [wheat[y]["None"] + wheat[y]["D"] + wheat[y]["S"] for y in wheat]
		fig2 = PlotData(self.wheat, wheat_supply, "Wheat Cents (1909-1958)")
		#fig2.suptitle("%d Wheat Pennies (1909-1958)" % sum(count))
		#fig2.tight_layout()

		return fig, fig2

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

def PlotData(coll, supply, title, fig=None):
	
	coll_totals = []
	coll_D_totals = []
	coll_S_totals = []
	supply_totals = []
	short_years = []
	for year in coll:
		tot = coll[year]["None"] + coll[year]["D"] + coll[year]["S"]
		coll_totals.append(tot)
		coll_D_totals.append(coll[year]["D"] + coll[year]["S"])
		coll_S_totals.append(coll[year]["S"])

		tot = (supply[year]["None"] + supply[year]["D"] + supply[year]["S"]) / 1e8
		supply_totals.append(tot)

		short_years.append(int(year)-1900)

	# find a way to divide the years (from 1970-1981) into nearly equal bins
	if 81 in short_years:
		num_divs = 2
		idx70 = short_years.index(70)
		total_70plus = coll_totals[idx70:]
		target_sum = sum(total_70plus) / num_divs
		divs = [0]*(num_divs-1)
		for i in range(len(total_70plus)):
			for j in range(num_divs):
				if divs[j] == 0:
					if sum(total_70plus[divs[max(0, j-1)]:i+1]) > target_sum:
						a = abs(sum(total_70plus[divs[max(0, j-1)]:i]) - target_sum)
						b = abs(sum(total_70plus[divs[max(0, j-1)]:i+1]) - target_sum)
						if a < b: divs[j] = i
						else: divs[j] = i+1
					break
			if divs[-1] != 0: break
		print("Divisions:")
		print([short_years[x+idx70] for x in divs])
	
	if fig == None:
		fig, ax = plt.subplots()
	else:
		ax = fig.add_subplot(2,1,2)

	fig.set_size_inches(10, 4)

	ax.bar(short_years, coll_totals)
	ax.bar(short_years, coll_D_totals)
	ax.bar(short_years, coll_S_totals)
	ax.legend(["P","D", "S"])
	if 81 in short_years:
		# Mark found division bins (from above) with axis lines and amount labels
		for i in range(num_divs-1):
			idx1 = (0 if i == 0 else divs[i-1]) + idx70
			idx2 = divs[i] + idx70
			y1 = short_years[idx1]
			y2 = short_years[idx2]
			plt.axvline(x=y2-0.5, color="black", linestyle="--", linewidth=0.7)
			plt.text((y1+y2)/2, ax.get_ylim()[1]*0.95, sum(coll_totals[idx1:idx2]))
		plt.text((short_years[divs[-1]+idx70] + 81)/2, ax.get_ylim()[1]*0.95, sum(coll_totals[divs[-1]+idx70:]))
		
		# 1959-1969 always gets its own bin
		plt.axvline(x=69.5, color="black", linestyle="--", linewidth=0.7)
		#plt.axvline(x=76.5, color="black", linestyle="--", linewidth=0.7)
		plt.text(64, ax.get_ylim()[1]*0.95, sum(coll_totals[:11]))
		#plt.text(73, ax.get_ylim()[1]*0.95, sum(coll_totals[11:18]))
		#plt.text(79, ax.get_ylim()[1]*0.95, sum(coll_totals[18:]))

		price_lb = GetCopperPrice()
		lbs = sum(coll_totals) * (0.95 * 3.11) / 453.6 # 3.11 g per penny, 95% copper, 453.6 g per pound
		title += " [Copper value \$%.2f, %.1f lbs @ \$%.2f/lb]" % (lbs * price_lb, lbs, price_lb)
	plt.xticks(rotation=-45)
	ax.set_xticks(short_years)
	ax.set_xticklabels(["'%d" % y for y in short_years])
	ax.grid(axis='y')
	ax.set_axisbelow(True)

	ax2 = ax.twinx()
	ax2.plot(short_years, supply_totals, color="red")
	ax2.set_ylim([0, ax2.get_ylim()[1]])
	ax2.set_ylabel("Total Mintage (100 million)")

	fig.suptitle("%d %s" % (sum(coll_totals), title))
	fig.tight_layout()

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
