var timer;
var timerVal = 0;
var timerMax = 300;
var ringMax = 300;

var color0 = "#007FFF";
var color1 = "#7F00DF"; //"#00FF7F";
var color = 0;

function displayStats() {
	txt = document.getElementById("stats");
	
	txt.innerHTML = txt.innerHTML + "\nCurrent Streak:\t\t\t" + data["current_streak"];
	txt.innerHTML = txt.innerHTML + "\nLongest Streak:\t\t\t" + data["best_streak"];
	txt.innerHTML = txt.innerHTML + "\nTotal Sessions:\t\t\t" + data["sessions"];
	txt.innerHTML = txt.innerHTML + "\nTotal Mindfulness Minutes:\t" + data["total"];

	if (data["total"] > 60)
		txt.innerHTML = txt.innerHTML + minutesBreakdown(data["total"]);
}

function minutesBreakdown(minutes) {
	var days = 0;
	var hours = 0;
	
	days = parseInt(minutes / 1440);
	minutes = minutes % 1440;
	hours = parseInt(minutes / 60);
	minutes = minutes % 60;

	if (days > 0)
		strTime = days + "d " + hours + "h " + minutes + "m";
	else
		strTime = hours + "h " + minutes + "m";

	return " (" + strTime + ")";
	
}

function startTimer(evt) {
	document.getElementById("StartBtn").style.display = "none";
	document.getElementById("StopBtn").style.display = "block";

	ring.colorBg = "#404040";
	ring.setText("00:00");
	color = 0;
	ring.draw(true);

	var userTime = parseInt(document.getElementById("duration").value, 10);
	timerMax = userTime * 60;
	timer = setInterval(updateRing, 1000);
}

function stopTimer() {
	clearInterval(timer);

	if (timerVal >= 60) {
		$.ajax({
			url: "/post",
			type: "post",
			data: "cmd=ADD&type=Mind&duration="+(timerVal/60),
			success: function(res, textStatus) {
				alert("Completed mindfulness session!");
			}
		});
	}

	timerVal = 0;

	document.getElementById("StartBtn").style.display = "block";
	document.getElementById("StopBtn").style.display = "none";
}

function updateRing() {
	timerVal = timerVal + 1;
	if (timerVal > timerMax) {
		timerVal = timerVal - 1;
		stopTimer();
		return;
	}

	var minutes = timerVal / 60;
	var seconds = Math.round((minutes - Math.floor(minutes)) * 60);
	minutes = Math.floor(minutes);
	var timestr = minutes.toString().padStart(2, '0') + ':' + seconds.toString().padStart(2, '0');
	var value = (timerVal % ringMax) / ringMax;	

	ring.setValue(value);
	ring.setText(timestr);
	
	if (timerVal % ringMax == 0) {
		color = -1 * color + 1;
		if (color) {
			ring.colorBg = color0;
			ring.colorFg = color1;
		} else {
			ring.colorBg = color1;
			ring.colorFg = color0;
		}
		ring.noAnimations=true;
		ring.draw(true);
		ring.noAnimations=false;
	}
}

function setTimerMax(maxVal) {
	
}

function trueNightMode() {
	var checkbox = document.getElementById("trunite");
	var doc = document.body;
	var alltext = document.getElementById("everything");
	var startBtn = document.getElementById("StartBtn");
	var stopBtn = document.getElementById("StopBtn");
	var navbar = document.getElementsByClassName("active")[0];
	var hamburger = document.getElementsByClassName("icon")[0];
	var ringtext = ring.text;

	if (checkbox.checked == true) {
		doc.style.backgroundColor = "#101010";
		alltext.style.color = "#989898";
		startBtn.style.color = "#989898";
		startBtn.style.backgroundColor = "#304080";
		startBtn.style.boxShadow = "inset 0px 1px 0px 0px #344E79";
		stopBtn.style.color = "#989898";
		stopBtn.style.backgroundColor = "#304080";
		stopBtn.style.boxShadow = "inset 0px 1px 0px 0px #344E79";
		color0 = "#005FAF";
		color1 = "#5F309F";
		ringtext.style.color = "#969696";
		navbar.style.backgroundColor = "#5060A0";
		hamburger.style.backgroundColor = "#5060A0";
	} else {
		doc.style.backgroundColor = "#1E1E1E";
		alltext.style.color = "#C8C8C8";
		startBtn.style.color = "#C8C8C8";
		startBtn.style.backgroundColor = "#405090";
		startBtn.style.boxShadow = "inset 0px 1px 0px 0px #445E89";
		stopBtn.style.color = "#C8C8C8";
		stopBtn.style.backgroundColor = "#405090";
		stopBtn.style.boxShadow = "inset 0px 1px 0px 0px #445E89";
		color0 = "#007FFF";
		color1 = "#00FF7F";
		ringtext.style.color = "#C8C8C8";
		navbar.style.backgroundColor = "#7080C0";
		hamburger.style.backgroundColor = "#7080C0";
	}
	if (color) {
		ring.colorBg = color0;
		ring.colorFg = color1;
	} else {
		if (timerVal < ringMax)
			ring.colorBg = "#404040";
		else
			ring.colorBg = color1;
		ring.colorFg = color0;
	}
	ring.noAnimations=true;
	ring.draw(true);
	ring.noAnimations=false;
}
/*var bar = new ProgressBar.Circle(container, {
	color: '#aaa',
	// This has to be the same size as the maximum width to
	// prevent clipping
	strokeWidth: 4,
	trailWidth: 1,
	//easing: 'None',
	duration: 10000,
	text: {
		autoStyleContainer: false
	},
	from: { color: '#aaa', width: 1 },
	to: { color: '#333', width: 4 },
	// Set default step function for all animate calls
	step: function(state, circle) {
		circle.path.setAttribute('stroke', state.color);
		circle.path.setAttribute('stroke-width', state.width);

		var value = Math.round(circle.value() * this.duration);
		var minutes = value / 1000 / 60.0;
		var seconds = Math.round((minutes - Math.floor(minutes)) * 60);
		minutes = Math.floor(minutes);
		var timestr = minutes.toString().padStart(2, '0') + ':' + seconds.toString().padStart(2, '0');
		if (value === 0) {
			circle.setText('');
		} else {
			circle.setText(timestr);
		}

	}
});

bar.text.style.fontFamily = '"Raleway", Helvetica, sans-serif';
bar.text.style.fontSize = '2rem';

bar.animate(1.0);	// Number from 0.0 to 1.0*/
