import time
from datetime import datetime
import requests
import locale
import copy
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

locale.setlocale(locale.LC_ALL, '')
MAX_CHANGE = 5

class StonkTracker():
	def __init__(self):
		self.portfolio = readData()
		self.prev_state = copy.deepcopy(self.portfolio)
		self.init = False
		self.last_updated = 0
	
	def getPrices(self):
		tnow = time.time()
		tot_val = 0
		tot_cost = 0
		prev_val = 0
		for a in self.portfolio:
			if a == "TOTAL": continue
			asset = self.portfolio[a]
			if asset["quantity"] == 0: continue
			if asset["type"] == "stock":
				price, change = getStockQuote(asset["symbol"])
			elif asset["type"] == "crypto":
				price, change = getCryptoQuote(asset["symbol"])
			elif asset["type"] == "cash":
				price, change = (1.0, 0.0)
			else:
				price, change = (asset["est_val"], 0)

			if price > 0:
				value = price * asset["quantity"]
			else: # unable to retrieve latest price info
				# use either the previous state value or est_val
				if a in self.prev_state and "value" in self.prev_state[a]:
					value = self.prev_state[a]["value"]
				else:
					value = asset["est_val"]

			asset["value"] = value
			asset["est_val"] = value
			asset["pnl"] = value - asset["cost"]
			asset["day_change"] = change
			asset["mark"] = price
			
			tot_val += value
			tot_cost += asset["cost"]
			prev_val += value / (1 + change/100)

		self.portfolio["TOTAL"] = {
				"value": tot_val,
				"cost": tot_cost,
				"pnl": tot_val-tot_cost,
				"day_change": (tot_val-prev_val)/prev_val*100
		}
		self.init = True
		self.last_updated = tnow

	def getPortfolio(self):
		self.getPrices()
		invst = []
		hdrs = ["Asset", "% Chng Today", "Value", "Cost", "P/L"]
		sorted_assets = sorted([a for a in self.portfolio.keys() if a != "TOTAL"]) + ["TOTAL"]
		for a in sorted_assets:
			temp = {}
			asset = self.portfolio[a]
			if a != "TOTAL" and asset["quantity"] == 0: continue
			temp[hdrs[0]] = a 												# Asset name
			temp[hdrs[1]] = "%.2f%%" % asset["day_change"]					# % change today
			temp[hdrs[2]] = locale.currency(asset["value"], grouping=True)	# Value in USD
			temp[hdrs[3]] = locale.currency(asset["cost"], grouping=True)	# Cost in USD
			temp[hdrs[4]] = "%s (%d%%)" % (
				locale.currency(asset["pnl"], grouping=True),
				(asset["value"]/asset["cost"]-1)*100
			)																# Profit/Loss (%)
			temp["Color"] = self.getColorFromChange(asset["day_change"])	# Color hex code
			invst.append(temp)	
		return {"Headers":hdrs, "Investments":invst}

	def getNetWorth(self, asstr=False):
		tot_value = 0
		if (time.time() - self.last_updated) > 300:
			self.getPrices()
		for asset in self.portfolio:
			if asset == "TOTAL": continue
			tot_value += self.portfolio[asset]["value"]

		if asstr:
			return locale.currency(tot_value, grouping=True)
		else:
			return tot_value

	def getAllocations(self):
		allocations = {}
		for asset in self.portfolio:
			if asset == "TOTAL": continue
			allocations[asset] = self.portfolio[asset]["value"] / self.portfolio["TOTAL"]["value"]

		return allocations

	def getAllocation(self, asset):
		alloc_percent = self.portfolio[asset]["value"] / self.portfolio["TOTAL"]["value"]
		return alloc_percent

	def getInvestmentInfo(self, asset):
		ret = dict(self.portfolio[asset])
		ret["alloc"] = "%.1f%%" % (self.getAllocation(asset) * 100)
		return ret

	def getColorFromChange(self, score):
		diff = min(1, abs(score / MAX_CHANGE))
		if score < 0:
			r = "%0.2X" % int(224*diff + 250*(1-diff))
			g = "%0.2X" % int(64*diff + 216*(1-diff))
			b = "%0.2X" % int(64*diff + 216*(1-diff))
		# fade from yellow to red as score approaches max score
		elif score > 0:
			r = "%0.2X" % int(64*diff + 216*(1-diff))
			g = "%0.2X" % int(224*diff + 250*(1-diff))
			b = "%0.2X" % int(64*diff + 216*(1-diff))
		else:
			return "#E0E0E0"
		return "#%s%s%s" % (r, g, b)

	def addInvestment(self, name, symbol, quantity, amount, asset_type):
		if not name or not symbol:
			return "Invalid Name or Symbol"

		self.prev_state = copy.deepcopy(self.portfolio)
		if name in self.portfolio:
			self.portfolio[name]["quantity"] += quantity
			self.portfolio[name]["cost"] += amount
		else:
			self.portfolio[name] = {
				"symbol": symbol,
				"quantity": quantity,
				"cost": amount,
				"type": asset_type,
				"est_val": amount
				}
		saveData(self.portfolio)
		return "sall good"

	def editInvestment(self, name, quantity, amount):
		if not name or name not in self.portfolio:
			return "Invalid name"

		self.prev_state = copy.deepcopy(self.portfolio)
		self.portfolio[name]["quantity"] = quantity
		self.portfolio[name]["cost"] = amount

		saveData(self.portfolio)
		return "sall good"
	
def readData():
	data = []
	investments = {}
	with open("data/investments.csv", 'r') as f:
		data = f.readlines()
	data = data[1:]
	data = [d.replace("\n","").split(',') for d in data]
	for a in data:
		if float(a[2]) == 0: continue
		investments[a[0]] = {
			"symbol": a[1],
			"quantity": float(a[2]),
			"cost": float(a[3]),
			"type": a[4],
			"est_val": float(a[5]) if a[5] != "" else -1
		}
	return investments

def saveData(data):
	with open("data/investments.csv", 'w') as f:
		f.write("Name,Symbol,Quantity,Cost,Type,EstValue\n")

		for a in data:
			asset = data[a]
			if a == "TOTAL": continue

			f.write("%s,%s,%f,%f,%s,%s\n" % 
				(a, asset["symbol"], asset["quantity"], asset["cost"], asset["type"], 
				"" if asset["est_val"] == -1 else str(asset["est_val"])))

def readStats():
	stats = []
	with open("data/networth.csv", 'r') as f:
		stats = f.readlines()
	stats = [x.replace("\n", "") for x in stats[1:]]
	return stats


def getStockQuote(symbol):
	url = "https://query2.finance.yahoo.com/v8/finance/chart/"
	user_agent_headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

	resp = requests.get(url=url + symbol, headers=user_agent_headers)
	last_price = resp.json()["chart"]["result"][0]["meta"]["regularMarketPrice"]
	prev_close = resp.json()["chart"]["result"][0]["meta"]["chartPreviousClose"]
	change = (last_price - prev_close) / prev_close * 100
	return last_price, change

def getCryptoQuote(symbol):
	#url = "https://api.gemini.com/v1/pubticker/%sUSD"
	url = "https://api.gemini.com/v2/candles/%sUSD/1day"
	resp = requests.get(url % symbol)

	if resp.status_code != 200:
		print("Err: (%d) %s" % (resp.status_code, resp.text))
		return 0, 0
	last_price = resp.json()[0][4]
	prev_close = resp.json()[1][4]
	change = (last_price - prev_close) / prev_close * 100
	return last_price, change

def plotStats(curr_val=0):
	stats = readStats()
	month_str = ["None", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
	curr_month = int(time.strftime("%m", time.localtime(time.time())))
	curr_year = int(time.strftime("%y", time.localtime(time.time())))
	pastyear_cutoff = time.time() - 365*86400

	xticks = []
	xlabels = []
	data = []
	prev_label = ""
	for i in range(len(stats)):
		splitted = stats[i].split(",")
		timestamp = int(splitted[0])
		value = float(splitted[1])

		if timestamp <= pastyear_cutoff: continue
		month = time.strftime("%b", time.localtime(timestamp))
		if month != prev_label:
			xticks.append(i)
			xlabels.append(month)
			prev_label = month

		data.append(value)
	if curr_val:
		data.append(curr_val)

	fig = plt.figure()
	plt.plot(data)
	ax = plt.gca()

	plt.title("Portfolio Performance")
	plt.grid(True, "major", "x", linestyle="--", linewidth=1)
	plt.xticks(xticks, xlabels)
	yticks = ax.get_yticks()
	ylabels = ["$%dk" % (y/1000) for y in yticks]
	plt.yticks(yticks, ylabels)

	fig.tight_layout()
	return fig

def portfolioPieChart(allocations):
	labels = []
	sizes = []
	other = 0
	colors = ["#E06464", "#2D96E0", "#6EAF60", "#E09660", "#A078C8", "#A0A0A0"]

	sorted_assets = sorted(allocations.keys(), key=lambda x: allocations[x], reverse=True)
	for asset in sorted_assets:
		if len(labels) == 5:#allocations[asset] < 0.05:
			other += allocations[asset]*100
		else:
			labels.append(asset)
			sizes.append(allocations[asset]*100)
	if other > 0:
		labels.append("Other")
		sizes.append(other)

	fig, ax = plt.subplots()
	tmp, tmp, autotexts = ax.pie(sizes, labels=labels, colors=colors, autopct="%1.1f%%", pctdistance=0.75, shadow=False)
	for at in autotexts:
		at.set_color("white")
	
	center_circle = plt.Circle((0,0), 0.5, fc="white")
	ax.add_artist(center_circle)

	ax.axis("equal")
	plt.title("Portfolio Allocation")

	return fig

if __name__ == "__main__":
	print("Not intended to be run as main program")
