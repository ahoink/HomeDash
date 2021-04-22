from flask import Flask, request, render_template, Response, send_from_directory
from functools import wraps
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import io
import base64
import json
import time

import TaskTracker
import ExpenseTracker
import sun_azimuth
import NetworkTracker
import PlantTracker
import Weather
import CoinTracker

app = Flask(__name__)
task_proc = TaskTracker.TaskTracker()
exp_proc = ExpenseTracker.ExpenseTracker()
plant_proc = PlantTracker.PlantTracker()
coin_proc = CoinTracker.CoinTracker()

# HELPER FUNCTIONS
def readConfig():
	data = []
	config = {}
	with open("data/homedash.conf", 'r') as f:
		data = f.readlines()
	
	for line in data:
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
		elif cat == "owm_key":
			config["OWM_KEY"] = splitted[1]
		else:
			print("Unknown category '%s'" % cat) 
	return config

def check_auth(username, password):
    return username == "" and password == ""

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
	min_elev = 10 #config["min_elev"]
	max_elev = 36 #config["max_elev"]
	start,end = sun_azimuth.getSunlightTimes(lat, lon, angle, min_elev, max_elev)

	# get weather data
	wdata = Weather.formatWeatherData(Weather.getCurrentWeather(lat, lon, config["OWM_KEY"]))

	# combine all data objects
	data["tasks"] = tdata
	data["expenses"] = exdata
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
	fig,stats = TaskTracker.plotStats()
	output = io.BytesIO()
	FigureCanvas(fig).print_png(output)
	imagestr = "data:image/png;base64,"
	imagestr += base64.b64encode(output.getvalue()).decode("utf8")
	return render_template("stats.html", image=imagestr, stats=stats)

@app.route("/expenses")
def expensePage():
	data = exp_proc.getExpenseList()
	fig,stats = ExpenseTracker.plotStats()
	output = io.BytesIO()
	FigureCanvas(fig).print_png(output)
	imagestr = "data:image/png;base64,"
	imagestr += base64.b64encode(output.getvalue()).decode("utf8")
	return render_template("expenses.html", data=data, image=imagestr, stats=stats)

@app.route("/plants")
def plantsPage():
	data = plant_proc.getPlantList()
	return render_template("plants.html", data=data)

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

@app.route("/post", methods=["POST"])
def postData():
	cmd = request.form["cmd"]
	cmdType = request.form["type"]
	print(cmd, cmdType)
	if cmd == "ADD":
		if cmdType == "Task":
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
		elif cmdType == "Plant":
			res = plant_proc.addPlant(request.form["pname"])
		elif cmdType == "Coin":
			res = coin_proc.addPenny(request.form["year"], request.form["mintmark"])
		else:
			print("Invalid command type '%s'" % cmdType)
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
			print("Invalid command type '%s'" % cmdType)
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
			print("Invalid command type '%s'" % cmdType)
	return json.dumps(res)




if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6567, debug=False)
