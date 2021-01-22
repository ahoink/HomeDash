// --- FUNCTIONS --- //
function setTextFromData(selector, data)
{
	var txt = document.getElementById(selector);
	txt.innerHTML = data["val"];
	txt.style.color = data["color"];
}

function setHostStatus(data)
{
	const hosts = Object.keys(data);
	for (var i = 0; i < hosts.length; i++) {
		var statusCircle = document.getElementById("st_host" + String(i+1)); 
		document.getElementById("txt_host" + String(i+1)).innerHTML = hosts[i];
		if (data[hosts[i]]) {
			statusCircle.style.backgroundColor = "#40E000";
		}
		else {
		statusCircle.style.backgroundColor = "#E04000";	
		}
	}
}

function setWeatherInfo(data)
{
	var current = document.getElementById("current");
	var currentIcon = "wi wi-owm-" + data["d_n"] + "-" + data["wid"];
	var hourly = document.getElementById("hourly");
	var hourlyTimes = document.getElementById("hourlyTime");

	current.innerHTML = " " + data["temp"]["actual"] + "&#176F (feels like " + data["temp"]["feels"] + "&#176F) | " + data["humidity"] + "% humid";
	$("#currentIcon").addClass(currentIcon);
	var table = document.getElementById("weatherTbl");
	for (var i = 0; i < data["hourly"].length; i++)
	{
		var hr_icon = "wi wi-owm-" + data["hourly"][i]["d_n"] + "-" + data["hourly"][i]["wid"];
		var icon = document.getElementById("icon_hr" + String(i+1));
		table.rows[0].cells[i].innerHTML = data["hourly"][i]["time"];
		table.rows[1].cells[i].innerHTML = data["hourly"][i]["temp"]["actual"] + "&#176F";
		$("#icon_hr" + String(i+1)).addClass(hr_icon);
		
	}
}

// Dynamically create table with rows and columns based on data passed in
function constructTable(selector, data, type)
{
	var hdrs = data["Headers"]
	var items = data[type]
	$(selector + ' tr').remove();            // remove table if it already exists
	if (items.length <= 0)
	{
		if (type == "Tasks")
			document.getElementById('due_today').innerHTML = "<b>No Tasks Due Today!</b>";
		else if (type == "Expenses")
			document.getElementById('exp_due_week').innerHTML = "<b>No Expenses Due this Week!</b>";
		return;
	}
	var cols = Headers(hdrs, selector); // extract columns from headers
	for (var i = 0; i < items.length; i++)
	{
		var row = $('<tr/>');
		for (var colIdx = 0; colIdx < cols.length; colIdx++)
		{
			var val = items[i][cols[colIdx]];
			if (val == null) val = "";
				row.append($('<td/>').html(val));
		}

		// Set row color to color passed from python backend
		row[0].style.backgroundColor=items[i]["Color"]
		$(selector).append(row);
	}
}

// Columns based on number of headers (number of elements in each task entry)
function Headers(list, selector)
{
	var columns = [];
	var header = $('<tr/>');

	for (var i = 0; i < list.length; i++)
	{
		var k = list[i];
		if ($.inArray(k, columns) == -1)
		{
			columns.push(k);
			header.append($('<th/>').html(k));
		}
	}
	$(selector).append(header);
		return columns;
}

// Handle clicking a row in the Table
function handleClick(evt)
{
	// Display loading spinner
	document.getElementById("loader").style.display="block";

	var node = evt.target || evt.srcElement;                    // node clicked in event
	var idx = node.parentNode.rowIndex - 1                      // index of row minus 1 to ignore header row
	var name = String(node.parentNode.childNodes[0].innerText)  // text of first entry of row (task name)
	if (node.parentNode.childNodes[2].innerText == "DONE")
	{
		document.getElementById("loader").style.display="none";
		return;
	}
	$.ajax({
		url: "/post",
		type: "post",
		data: "cmd=UPDATE&type=Task&task="+name,
		success: function(data, textStatus, res) {
			data = $.parseJSON(data);
			node.parentNode.childNodes[1].innerText=data[0]     // re-set last completed date
			node.parentNode.childNodes[2].innerText=data[1]     // re-set due time
			node.parentElement.style.backgroundColor="#80FF80"  // reset row color to green
			document.getElementById("loader").style.display="none"; // turn off loading spinner
		}
	});
}

function perUpdate()
{
	$.get("/getsummary", function(data, status) {
		setTextFromData('prod_val', data["prod"]);
		setTextFromData('exp_val', data["exp"]);
		constructTable('#table', data["tasks"], "Tasks")
		setHostStatus(data["ping"]);
		setWeatherInfo(data["weather"]);
	});
}
