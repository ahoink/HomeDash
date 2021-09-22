import time
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import copy

MAX_SCORE = 86400*30

class ExpenseTracker():
	def __init__(self):
		self.expenses = readData()
		self.prev_state = copy.deepcopy(self.expenses)
	
	def getExpenseList(self, weekOnly=False):
		exps = []
		hdrs = ["Expense", "Amount", "Due", "Autopay"]
		auto_var = []
		sorted_expenses = sorted(self.expenses.keys(), key=lambda x: self.expenses[x]["due"]) # sort in order of due date
		tnow = time.time()
		for e in sorted_expenses:
			temp = {}
			#due_date = ""
			expense = self.expenses[e]
			if expense["autopay"] and tnow > expense["due"] + 86400:	# autopay enabled and past due
				if expense["variable"]: # variable, ask user for amount via javascript
					auto_var.append(e)
				else: # not variable, simply update as usual and reset the timestamp
					expense["due"] = self.updateExpense(e, ret_ts=True)
			temp[hdrs[0]] = e	 													# Expense name
			temp[hdrs[1]] = "$%.2f" % expense["amount"]								# Amount (or average/predicted)
			temp[hdrs[2]] = time.strftime("%b %d", time.localtime(expense["due"]))	# Due Date (Month Date)
			temp[hdrs[3]] = "Yes" if expense["autopay"] else "No"					# Autopay enabled
			temp["Color"] = self.getColorFromDate(expense["due"])					# Color hex code
			temp["isVar"] = expense["variable"]
			if weekOnly and abs(expense["due"] - tnow) > 86400*7:
				continue
			exps.append(temp)	
		return {"Headers":hdrs, "Expenses":exps, "Auto-vari":auto_var}

	def getBalance(self):
		curr_month = time.strftime("%b", time.localtime(time.time()))
		due_this_month = [self.expenses[e]["amount"] for e in self.expenses if\
		 	time.strftime("%b", time.localtime(self.expenses[e]["due"])) == curr_month and\
			(self.expenses[e]["due"] > time.time())]
		balance = sum(due_this_month)
		color = "black"
		return {"val": "$%.2f" % balance, "color": color}

	def getExpenseInfo(self, exp_name):
		temp = dict(self.expenses[exp_name])
		temp["due"] = time.strftime("%d", time.localtime(temp["due"]))
		return temp

	def getColorFromDate(self, t):
		# generate hex string of color based on the score (lowest RGB value is 128 so the color is lighter and softer)
		# Start as green and fade to yellow as score approaches half of the max score
		diff = t - time.time()
		warning = 86400*7
		maxdiff = 86400*30
		if diff >= maxdiff:	# more than a month is green
			return "#80FF80"
		elif diff >= warning: # fade to yellow as approach one week away
			r = "%0.2X" % int(255 - 127 * ((diff - warning) / (maxdiff-warning)))
			g = "FF"
			b = "80"
		# fade from yellow to red as diff approaches one day
		elif diff > 86400 :
			r = "FF"
			g = "%0.2X" % int(128 + 127 * ((diff - 86400) / (warning - 86400)))
			b = "80"
		else: # red for a day or less
			return "#FF8080"
		return "#%s%s%s" % (r, g, b)

	def incrementDate(self, t):
		dt = datetime.fromtimestamp(t)
		if dt.month == 12:
			new_dt = datetime(dt.year+1, 1, dt.day, 12, 0, 0)
		else:
			if dt.day >= 29 and dt.month == 1:
				new_dt = datetime(dt.year, dt.month+1, 28, 12, 0, 0)
			else:
				new_dt = datetime(dt.year, dt.month+1, dt.day, 12, 0, 0)
		return int(new_dt.timestamp())

	def addExpense(self, name, amount, date, autopay, isvar):
		if not name or name in self.expenses:
			return "Invalid Name"
		if not date or not amount:
			return "Invalid Date"

		if date.isdigit():
			date = dateNumToTimestamp(int(date))
		else:
			return "Invalid Date"

		try:
			amount = float(amount)
		except:
			return "Invalid amount"

		# save the current state and add the new expense with last completed time as now
		self.prev_state = copy.deepcopy(self.expenses)
		self.expenses[name] = {
			"amount": amount,
			"due": date,
			"autopay": autopay,
			"variable": isvar
		}
		saveData(self.expenses)
		return "sall good"
	
	def updateExpense(self, exp_name, amount=None, ret_ts=False):
		tnow = time.time()
		
		# CC, remove tracked expenses that are paid on CC
		if exp_name == "Amazon CC":
			pass
			#templist = [x for x in self.expenses if x[0] == "Internet"][0]
			#amount = float(amount) - float(templist[1])

		# save the current state before updating
		self.prev_state = copy.deepcopy(self.expenses)

		# save the expense and score upon completion to the stats file
		if amount != None and amount != "null":
			self.expenses[exp_name]["amount"] = float(amount)
		saveStats(exp_name, self.expenses[exp_name], tnow)

		# update expense last completed time and save to file
		self.expenses[exp_name]["due"] = self.incrementDate(self.expenses[exp_name]["due"])
		saveData(self.expenses)
		
		# return epoch timestamp		
		if ret_ts: return self.expenses[exp_name]["due"]

		resp = [time.strftime("%b %d", time.localtime(self.expenses[exp_name]["due"])), self.expenses[exp_name]["amount"]]
		return resp

	def editExpense(self, name, amount, due, isAuto, isVari):
		if not name or name not in self.expenses:
			return "Invalid Name"

		if not due or (not due.isdigit() and due.lower() != "eom"):
			return "Invalid Due Date"
		
		if due.lower() == "eom":
			due = 30 # TODO: make EOM functional to always use the last day of a given month
		
		self.prev_state = copy.deepcopy(self.expenses)
		
		self.expenses[name]["amount"] = amount
		self.expenses[name]["due"] = dateNumToTimestamp(int(due))
		self.expenses[name]["autopay"] = isAuto
		self.expenses[name]["variable"] = isVari

		saveData(self.expenses)

		return "sall good"

	def revertPrevState(self):
		if len(self.expenses.keys()) == len(self.prev_state.keys()):
			remLastStatEntry()
		self.expenses = copy.deepcopy(self.prev_state)
		saveData(self.expenses)
		return "sall good"

def readData():
	exps = {}
	data = []
	with open("data/expenses.csv", 'r') as f:
		data = f.readlines()
	data = data[1:]
	data = [e.replace("\n","").split(',') for e in data]
	for i in range(len(data)):
		name = data[i][0]
		if name[0] == "#": continue
		exps[name] = {
			"amount": float(data[i][1]),
			"due": int(data[i][2]),
			"autopay": data[i][3] == "1",
			"variable": data[i][4] == "1"
		}
	return exps

def saveData(data):
	with open("data/expenses.csv", 'w') as f:
		f.write("expense,amount,due,autopay,variable\n")
		for e in data:
			f.write("%s,%f,%d,%d,%d\n" % 
			(e, data[e]["amount"], data[e]["due"], data[e]["autopay"], data[e]["variable"]))

def readStats():
	data = []
	with open("data/expense_stats.csv", 'r') as f:
		data = f.readlines()
	data = [x.replace("\n","").split(',') for x in data]
	for i in range(len(data)):
		data[i][1] = int(data[i][1]) # timestamp
		data[i][2] = float(data[i][2]) # amount
	return data

def saveStats(exp_name, data, t):
	with open("data/expense_stats.csv", "a") as f:
		f.write("%s,%d,%f\n" % (exp_name, t, data["amount"]))

def remLastStatEntry():
	data = []
	with open("data/expense_stats.csv", 'r') as f:
		data = f.readlines()
	data = data[:-1]
	with open("data/expense_stats.csv", 'w') as f:
		for d in data:
			f.write(d)

def plotStats():
	data = readStats()
	expense_stats = {}
	month_stats = {}
	month_str = ["None", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
	curr_month = int(time.strftime("%m", time.localtime(time.time())))
	curr_year = int(time.strftime("%y", time.localtime(time.time())))
	old_cutoff = time.time() - 365*86400 # one year ago
	for i in range(len(data)):
		expense_name = data[i][0]
		expense_completed = data[i][1]
		expense_amt = data[i][2]

		# ignore data older than a year
		if expense_completed <= old_cutoff: continue

		month = int(time.strftime("%m", time.localtime(expense_completed)))
		year = int(time.strftime("%y", time.localtime(expense_completed)))
		if month == curr_month and year != curr_year: continue # ignore data from same month last year

		month_tot = month_stats.get(month, 0) + expense_amt
		month_stats[month] = month_tot
	
		# keep track of min, max, tot amount of variable expenses
		temp = expense_stats.get(expense_name, {"min":999999, "max":0, "tot":0, "cnt":0})
		temp["min"] = min(temp["min"], expense_amt)
		temp["max"] = max(temp["max"], expense_amt)
		temp["tot"] += expense_amt
		temp["cnt"] += 1
		expense_stats[expense_name] = temp

	# create javascript-friendly dict (to be read as JSON)
	js_stats = {}
	for e in expense_stats:
		min_amt = expense_stats[e]["min"]
		max_amt = expense_stats[e]["max"]
		avg_amt = expense_stats[e]["tot"] / expense_stats[e]["cnt"]
		if min_amt != max_amt:
			js_stats[e] = {"min":min_amt, "max":max_amt, "avg":round(avg_amt,2)}

	# sort so the current month is rightmost position
	months = sorted([m for m in month_stats])
	if 12 in months and 1 in months:
		if curr_month in months:
			while months[-1] != curr_month:
				months = months[1:] + [months[0]]
		else:
			while months[-1] != (curr_month - 1):
				months = months[1:] + [months[0]]
	vals = [month_stats[m] for m in months]
	
	# Make sure plot spans at least 6 months
	while len(vals) < 6:
		next_month = months[-1]+1
		if next_month > 12: next_month = 1
		months.append(next_month)
		vals.append(0)

	# only span X months
	span = 6
	span = min(span,len(vals))
	vals = vals[-span:]
	months = months[-span:]

	avg_monthly = sum(vals[:-1]) / (len(vals) - 1)

	# plot and format
	fig = plt.figure()
	plt.bar(range(len(vals)), vals)
	plt.xticks(range(len(vals)), [month_str[int(x)] for x in months])
	for i,v in enumerate(vals):
		if v == 0: continue	
		plt.text(i-0.4, v+15, "$%d" % (v+0.5))
	plt.plot([-1, len(vals)], [avg_monthly, avg_monthly], color="red", linestyle="--", linewidth=0.5)
	plt.xlim((-0.5, len(vals)-0.5))
	plt.text(-0.5-45/(496/span), avg_monthly, "$%d" % (avg_monthly+0.5), color="red")	

	return fig, js_stats

def secToTimeString(t):
	# only converts to days or months
	days = t / 86400
	if days <= 28:
		timestr = "%.2f d" % days
	else:
		timestr = "%.2f M" % (days / 30)
	return timestr

def dateNumToTimestamp(d):
	dt = datetime.fromtimestamp(time.time())
	if dt.day < d:
		temp = datetime(dt.year, dt.month, d, 12, 0, 0)
	else:
		if dt.month == 12:
			temp = datetime(dt.year+1, 1, d, 12, 0, 0)
		else:
			temp = datetime(dt.year, dt.month+1, d, 12, 0, 0)
	return int(temp.timestamp())

if __name__ == "__main__":
	print("Not intended to be run as main program")
