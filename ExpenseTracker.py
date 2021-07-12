import time
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

MAX_SCORE = 86400*30

class ExpenseTracker():
	def __init__(self):
		self.expenses = readData()
		self.prev_state = [[x for x in y] for y in self.expenses]
	
	def getExpenseList(self, weekOnly=False):
		exps = []
		hdrs = ["Expense", "Amount", "Due", "Autopay"]
		auto_var = []
		sorted_expenses = sorted(self.expenses, key=lambda x: x[2]) # sort in order of due date
		tnow = time.time()
		for t in sorted_expenses:
			temp = {}
			#due_date = ""
			if t[3] and tnow > t[2] + 86400:	# autopay enabled and past due
				if t[4]: # variable, ask user for amount via javascript
					auto_var.append(t[0])
				else: # not variable, simply update as usual and reset the timestamp
					t[2] = self.updateExpense(t[0], ret_ts=True)
			temp[hdrs[0]] = t[0] 											# Expense name
			temp[hdrs[1]] = "$%.2f" % t[1]									# Amount (or average/predicted)
			temp[hdrs[2]] = time.strftime("%b %d", time.localtime(t[2]))	# Due Date (Month Date)
			temp[hdrs[3]] = "Yes" if t[3] else "No"							# Autopay enabled
			temp["Color"] = self.getColorFromDate(t[2])						# Color hex code
			temp["isVar"] = t[4]
			if weekOnly and abs(t[2] - tnow) > 86400*7:
				continue
			exps.append(temp)	
		return {"Headers":hdrs, "Expenses":exps, "Auto-vari":auto_var}

	def getBalance(self):
		curr_month = time.strftime("%b", time.localtime(time.time()))
		due_this_month = [e[1] for e in self.expenses if time.strftime("%b", time.localtime(e[2])) == curr_month and (e[2] > time.time())]
		balance = sum(due_this_month)
		color = "black"
		return {"val": "$%.2f" % balance, "color": color}

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
		if not name or name in [n[0] for n in self.expenses]:
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
		self.prev_state = [[x for x in y] for y in self.expenses]
		self.expenses.append([name, amount, date, autopay, isvar])
		saveData(self.expenses)
		return "sall good"
	
	def updateExpense(self, exp_name, amount=None, ret_ts=False):
		tnow = time.time()
		# get sublist from expense list where name matches expense_name and get the index of that sublist
		sublist = [x for x in self.expenses if x[0] == exp_name][0]
		idx = self.expenses.index(sublist)
		
		# CC, remove tracked expenses that are paid on CC
		if exp_name == "Amazon CC":
			templist = [x for x in self.expenses if x[0] == "Internet"][0]
			amount = float(amount) - float(templist[1])

		# save the current state before updating
		self.prev_state = [[x for x in y] for y in self.expenses]

		# save the expense and score upon completion to the stats file
		if amount != None and amount != "null":
			sublist[1] = float(amount)
			self.expenses[idx][1] = float(amount)
		saveStats(sublist, tnow)

		# update expense last completed time and save to file
		self.expenses[idx][2] = self.incrementDate(self.expenses[idx][2])
		saveData(self.expenses)
		
		# return epoch timestamp		
		if ret_ts: return self.expenses[idx][2]

		resp = [time.strftime("%b %d", time.localtime(self.expenses[idx][2])), self.expenses[idx][1]]
		return resp

	def revertPrevState(self):
		if len(self.expenses) == len(self.prev_state):
			remLastStatEntry()
		self.expenses = [[x for x in y] for y in self.prev_state]
		saveData(self.expenses)
		return "sall good"

def readData():
	exps = []
	with open("data/expenses.csv", 'r') as f:
		exps = f.readlines()
	exps = exps[1:]
	exps = [e.replace("\n","").split(',') for e in exps]
	for i in range(len(exps)):
		exps[i][1] = float(exps[i][1])	# amount
		exps[i][2] = int(exps[i][2])	# due timestamp
		exps[i][3] = exps[i][3] == "1"	# autopay enabled
		exps[i][4] = exps[i][4] == "1"	# amount varies
	return exps

def saveData(data):
	with open("data/expenses.csv", 'w') as f:
		f.write("expense,amount,due,autopay,variable\n")
		for e in data:
			f.write("%s,%f,%d,%d,%d\n" % (e[0], e[1], e[2], e[3], e[4]))

def readStats():
	data = []
	with open("data/expense_stats.csv", 'r') as f:
		data = f.readlines()
	data = [x.replace("\n","").split(',') for x in data]
	for i in range(len(data)):
		data[i][1] = int(data[i][1]) # timestamp
		data[i][2] = float(data[i][2]) # amount
	return data

def saveStats(data, t):
	with open("data/expense_stats.csv", "a") as f:
		f.write("%s,%d,%f\n" % (data[0], t, data[1]))

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
