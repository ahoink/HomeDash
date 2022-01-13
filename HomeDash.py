from flask import Flask, request, render_template, Response, send_from_directory
from functools import wraps
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import io
import base64
import json
import time

import TaskTracker
import ExpenseTracker
import StonkTracker
import sun_azimuth
import NetworkTracker
import PlantTracker
import MindTracker
import Weather
import CoinTracker

app = Flask(__name__)
task_proc = TaskTracker.TaskTracker()
exp_proc = ExpenseTracker.ExpenseTracker()
inv_proc = StonkTracker.StonkTracker()
plant_proc = PlantTracker.PlantTracker()
mind_proc = MindTracker.MindTracker()
coin_proc = CoinTracker.CoinTracker()

# HELPER FUNCTIONS
def LogEvent(evt):
	with open("data/Events.log", 'a') as f:
		f.write("%s\n" % evt)

def ReadLogs():
	logs = []
	today = time.time()
	thirty_days_ago = today - 86400*30
	idx_30 = 0

	try:
		with open("data/Events.log", 'r') as f:
			logs = f.readlines()
	except:
		return ["No logs"]

	for i in range(len(logs)):
		logs[i] = logs[i].replace("\n", "")
		if logs[i] == "": continue

		idx = logs[i].find(" ")
		epoch = int(logs[i][:idx])
		if epoch < thirty_days_ago: idx_30 = i

		ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(epoch))
		logs[i] = "%s -- %s" % (ts, logs[i][idx+1:].replace("|", "--"))

	logs = logs[idx_30+1:]
	return logs[::-1]

def readConfig():
	data = []
	config = {}
	with open("data/homedash.conf", 'r') as f:
		data = f.readlines()
	
	for line in data:
		if line[0] == '#': continue
		# should be tab separated
		splitted = line.replace("\n", "").split()

		cat = splitted[0].lower()
		if cat == "host":
			temp_hosts = config.get("hosts", {})
			temp_hosts[splitted[1]] = splitted[2]
			config["hosts"] = temp_hosts
		elif cat == "lat" or cat == "latitude":
			config["lat"] = float(splitted[1])
		elif cat == "lon" or cat == "longitude":
			config["lon"] = float(splitted[1])
		elif cat == "angle":
			config["angle"] = int(splitted[1])
		elif cat == "angle_adj_lo":
			config["angle_adj_lo"] = int(splitted[1])
		elif cat == "angle_adj_up":
			config["angle_adj_up"] = int(splitted[1])
		elif cat == "owm_key":
			config["OWM_KEY"] = splitted[1]
		elif "elev" in cat:
			config[cat] = int(splitted[1])
		elif cat == "login":
			config["user"] = splitted[1]
			config["pass"] = splitted[2]
		else:
			print("Unknown category '%s'" % cat) 
	return config

def check_auth(username, password):
	config = readConfig()
	return username == config["user"] and password == config["pass"]

# MAIN FUNCTIONS
def authenticate():
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

def getHomeData(update=False):
	# get task, productivity, and expense data
	data = {}
	tdata = task_proc.getTaskList(todayOnly=True)
	exdata = exp_proc.getExpenseList(weekOnly=True)
	pldata = plant_proc.getPlantList(watchOnly=True)
	pdata = task_proc.getProductivity()
	edata = exp_proc.getBalance()
	wdata = {}
	ndata = {}
	
	config = readConfig()

	# ping local hosts
	#hosts = config["hosts"]
	#for h in hosts:
	#	ndata[h] = NetworkTracker.ping(hosts[h])

	# get sun data
	lat = config["lat"]
	lon = config["lon"]
	angle = config["angle"]
	angle_lo = config.get("angle_adj_lo", 65)
	angle_up = config.get("angle_adj_up", 65)
	min_elev = config.get("min_elev", 0)
	max_elev = config.get("max_elev", 90)
	start,end = sun_azimuth.getSunlightTimes(lat, lon, angle, angle_lo, angle_up, min_elev, max_elev)

	# get weather data
	wdata = Weather.formatWeatherData(Weather.getCurrentWeather(lat, lon, config["OWM_KEY"]))

	# combine all data objects
	data["tasks"] = tdata
	data["expenses"] = exdata
	data["plants"] = pldata
	data["prod"] = pdata
	data["exp"] = edata
	if not update: data["sunlight"] = {"start": start, "end": end}
	#data["ping"] = ndata
	data["weather"] = wdata

	return data


@app.route('/')
#@requires_auth
def index():
		data = getHomeData()
		return render_template("index.html", data=data)

# PAGES
@app.route("/tasks")
def tasksPage():
	data = task_proc.getTaskList()
	return render_template("tasks.html", data=data)

@app.route("/stats")
def statsPage():
	fig,stats, grid = TaskTracker.plotStats()
	output = io.BytesIO()
	FigureCanvas(fig).print_png(output)
	imagestr = "data:image/png;base64,"
	imagestr += base64.b64encode(output.getvalue()).decode("utf8")
	
	output = io.BytesIO()
	grid.save(output, format="PNG")
	imagestr2 = "data:image/png;base64,"
	imagestr2 += base64.b64encode(output.getvalue()).decode("utf8")
	return render_template("stats.html", image=imagestr, stats=stats, image2=imagestr2)

@app.route("/expenses")
def expensePage():
	data = exp_proc.getExpenseList()
	fig,stats = ExpenseTracker.plotStats()
	output = io.BytesIO()
	FigureCanvas(fig).print_png(output)
	imagestr = "data:image/png;base64,"
	imagestr += base64.b64encode(output.getvalue()).decode("utf8")
	return render_template("expenses.html", data=data, image=imagestr, stats=stats)

@app.route("/investments")
@requires_auth
def investmentPage():
	data = inv_proc.getPortfolio()
	fig = StonkTracker.plotStats(inv_proc.getNetWorth())
	fig2 = StonkTracker.portfolioPieChart(inv_proc.getAllocations())

	output = io.BytesIO()
	FigureCanvas(fig).print_png(output)
	imagestr = "data:image/png;base64,"
	imagestr += base64.b64encode(output.getvalue()).decode("utf8")	

	output = io.BytesIO()
	FigureCanvas(fig2).print_png(output)
	imagestr2 = "data:image/png;base64,"
	imagestr2 += base64.b64encode(output.getvalue()).decode("utf8")

	return render_template("investments.html", data=data, image=imagestr, image2=imagestr2)

@app.route("/plants")
def plantsPage():
	data = plant_proc.getPlantList()
	return render_template("plants.html", data=data)

@app.route("/mindfulness")
def mindfulPage():
	data = mind_proc.getStats()
	return render_template("mindfulness.html", data=data)

@app.route("/videos")
def videosPage():
	return render_template("videos.html")

@app.route("/coins")
def coinsPage():
	fig, fig2 = coin_proc.getPlots()

	output = io.BytesIO()
	FigureCanvas(fig).print_png(output)
	imagestr = "data:image/png;base64,"
	imagestr += base64.b64encode(output.getvalue()).decode("utf8")

	output = io.BytesIO()
	FigureCanvas(fig2).print_png(output)
	imagestr2 = "data:image/png;base64,"
	imagestr2 += base64.b64encode(output.getvalue()).decode("utf8")
	return render_template("coins.html", image=imagestr, image2=imagestr2)

@app.route("/logs")
def logsPage():
	data = ReadLogs()
	return render_template("logs.html", data=data)

@app.route('/favicon.ico')
def favicon():
	return send_from_directory("./static", "favicon.png", mimetype="image/png")

# ENDPOINTS
@app.route("/getlan", methods=["GET"])
def getLANStatus():
	config = readConfig()
	data = {}

	# ping local hosts
	hosts = config["hosts"]
	for h in hosts:
		data[h] = NetworkTracker.ping(hosts[h])

	return Response(json.dumps(data), mimetype="text/json")


@app.route("/gettasks", methods=["GET"])
def getTasks():
	data = task_proc.getTaskList()
	return Response(json.dumps(data), mimetype="text/json")

@app.route("/getsummary", methods=["GET"])
def getSummary():
	data = getHomeData(update=True)
	return Response(json.dumps(data), mimetype="text/json")

@app.route("/getexp", methods=["GET"])
def getExp():
	data = exp_proc.getExpenseList()
	return Response(json.dumps(data), mimetype="text/json")

@app.route("/getplants", methods=["GET"])
def getPlants():
	data = plant_proc.getPlantList()
	return Response(json.dumps(data), mimetype="text/json")

@app.route("/getinv", methods=["GET"])
def getInv():
	data = inv_proc.getPortfolio()
	return Response(json.dumps(data), mimetype="text/json")

@app.route("/post", methods=["POST"])
def postData():
	cmd = request.form["cmd"]
	cmdType = request.form["type"]
	res = ""

	# log event
	event_msg = "%d %s %s" % (time.time(), cmd, cmdType)
	params = ", ".join(["%s=%s" % (param, request.form[param]) for param in request.form if param != "cmd" and param != "type"])
	if params != "":
		event_msg += " | " + params
	LogEvent(event_msg)

	# handle command
	# ----- ADD ----- #
	if cmd == "ADD":
		if cmdType == "Task":
			if not request.form["tname"]:
				res = "Error: Task Name is required"
			elif not request.form["tfreq"]:
				res = "Error: Frequency is required"
			elif not request.form["tcost"]:
				res = "Error: Time Cost is required"
			elif not request.form["twt"]:
				res = "Error: Weight is required"
			else:
				res = task_proc.addTask(request.form["tname"],
									request.form["tfreq"],
									int(request.form["tcost"]), 
									int(request.form["twt"]))
		elif cmdType == "Expense":
			autopay = "autopay" in request.form
			isvar = "isvar" in request.form
			res = exp_proc.addExpense(request.form["name"],
										request.form["amt"],
										request.form["due"],
										autopay,
										isvar)
		elif cmdType == "Investment":
			res = inv_proc.addInvestment(request.form["name"], 
										request.form["sym"],
										float(request.form["qnt"]),
										float(request.form["amt"]),
										request.form["atype"])
		elif cmdType == "Plant":
			res = plant_proc.addPlant(request.form["pname"])
		elif cmdType == "Mind":
			res = mind_proc.addSession(int(float(request.form["duration"])))
		elif cmdType == "Coin":
			res = coin_proc.addPenny(request.form["year"], request.form["mintmark"])
		else:
			res = "Invalid command type '%s'" % cmdType
			print(res)
	# ----- EDIT ----- #
	elif cmd == "EDIT":
		if cmdType == "Task":
			if not request.form["e_cost"]:
				res = "Error: Time Cost is required"
			elif not request.form["e_wt"]:
				res = "Error: Weight is required"
			elif not request.form["e_last"]:
				res = "Error: Last Done is required"
			else:
				res = task_proc.editTask(
								request.form["e_name"],	
								request.form["e_freq"],
								int(request.form["e_cost"]),
								int(request.form["e_wt"]),
								int(request.form["e_last"]),
								"e_active" in request.form)
		elif cmdType == "Expense":
			if not request.form["e_amt"]:
				res = "Error: Amount is required"
			else:
				res = exp_proc.editExpense(
								request.form["e_name"],
								float(request.form["e_amt"]),
								request.form["e_due"],
								"e_auto" in request.form,
								"e_vari" in request.form)
		elif cmdType == "Investment":
			if not request.form["i_qnt"]:
				res = "Error: Quantity is required"
			elif not request.form["i_amt"]:
				res = "Error: Amount is required"
			else:
				res = inv_proc.editInvestment(
								request.form["i_name"],
								float(request.form["i_qnt"]),
								float(request.form["i_amt"]))
		else:
			res = "Invalid command type '%s'" % cmdType
			print(res)
	# ----- GET (info) ----- #
	elif cmd == "GET":
		if cmdType == "Task":
			res = task_proc.getTaskInfo(request.form["task"])
		elif cmdType == "Expense":
			res = exp_proc.getExpenseInfo(request.form["exp"])
		elif cmdType == "Investment":
			res = inv_proc.getInvestmentInfo(request.form["inv"])
		else:
			res = "Invalid command type '%s'" % cmdType
			print(res)
	# ----- UNDO ----- #
	elif cmd == "UNDO":
		if cmdType == "Task":
			res = task_proc.revertPrevState()
		elif cmdType == "Expense":
			res = exp_proc.revertPrevState()
		elif cmdType == "Plant":
			res = plant_proc.revertPrevState()	
		elif cmdType == "Coin":
			res = coin_proc.revertPrevState()
		else:
			res = "Invalid command type '%s'" % cmdType
			print(res)
	# ----- UPDATE ----- #
	elif cmd == "UPDATE":
		if cmdType == "Task":
			task_name = request.form["task"]
			res = task_proc.updateTask(task_name)
		elif cmdType == "Expense":
			res = exp_proc.updateExpense(request.form["exp"], request.form["amount"])
		elif cmdType == "Stats":
			sorting = int(request.form["sort_col"])
			res = TaskTracker.getStatsAvgBreakdown(sorting=sorting)
		elif cmdType == "Plant":
			plant_name = request.form["plant"]
			res = plant_proc.updatePlant(plant_name)
		elif cmdType == "Coin":
			res = coin_proc.saveData()
		else:
			res = "Invalid command type '%s'" % cmdType
			print(res)

	# Set action for next UNDO command
	if cmdType == "Task":
		if "task" in request.form:
			task_proc.setLastAction("%s %s" % (cmd, request.form["task"]))
		elif "tname" in request.form:
			task_proc.setLastAction("%s %s" % (cmd, request.form["tname"]))
		else:
			task_proc.setLastAction(cmd)

	if isinstance(res, str):
		LogEvent("%d RES (%s) | '%s'" % (time.time(), cmd, res))
	elif isinstance(res, list):
		LogEvent("%d RES (%s) | %s" % (time.time(), cmd, res[-1]))
	return json.dumps(res)




if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6567, debug=False)
