 // Dynamically create table with rows and columns based on data passed in
function constructTable(selector, data)
{
	var hdrs = data["Headers"];
	var tasks = data["Tasks"];
	$('#table tr').remove();            // remove table if it already exists
	var cols = Headers(hdrs, selector); // extract columns from headers
	for (var i = 0; i < tasks.length; i++)
	{
		var row = $('<tr/>');
		for (var colIdx = 0; colIdx < cols.length; colIdx++)
		{
			var val = tasks[i][cols[colIdx]];
			if (val == null) val = "";
				row.append($('<td/>').html(val));
		}

		// Set row color to color passed from python backend
		row[0].style.backgroundColor=tasks[i]["Color"];
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
	if (window.configureMode) {
		openConfForm(evt);
	}
	else {
		// Display loading spinner
		document.getElementById("loader").style.display="block";

		var node = evt.target || evt.srcElement;					// node clicked in event
		var idx = node.parentNode.rowIndex - 1;						// index of row minus 1 to ignore header row
		var name = String(node.parentNode.childNodes[0].innerText);	// text of first entry of row (task name)
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
				node.parentNode.childNodes[1].innerText=data[0];		// re-set last completed date
				node.parentNode.childNodes[2].innerText=data[1];		// re-set due time
				node.parentElement.style.backgroundColor="#80FF80";		// reset row color to green
				document.getElementById("loader").style.display="none"; // turn off loading spinner
			}
		});
	}
}

function submitNewTask()
{
	//e.preventDefault();
	data = $("#myForm").serialize(); // data entered by user
	data = "cmd=ADD&type=Task&"+data;
	$.ajax({
		url: "/post",
		type: "post",
		data: data,
		success: function(res, textStatus){
			if (res != "\"sall good\"")
			{
				alert(res);
			}
			else
			{
				alert("Successfully added task");
				document.getElementById("tname").value="";
				document.getElementById("tfreq").value="";
				document.getElementById("tcost").value="";
				document.getElementById("twt").value="";
				perUpdate();
			}
		}
	});
}

function editTask()
{
	data = $("#confTaskForm").serialize(); // data entered by user
	data = "cmd=EDIT&type=Task&"+data;
	$.ajax({
		url: "/post",
		type: "post",
		data: data,
		success: function(res, textStatus){
			if (res != "\"sall good\"")
			{
				alert(res);
			}
			else
			{
				closeConfForm();
				alert("Successfully modified task");
			}
		}
	});
}

function undoLastAction(evt)
{
	$.ajax({
		url: "/post",
		type: "post",
		data: "cmd=UNDO&type=Task",
		success: function(){
			alert("Undo Successful - Previous state restored");
			perUpdate();
		}
	});
}

function configureTracker(evt)
{
	window.configureMode = !window.configureMode;
	if (window.configureMode)
		document.getElementById("confBtn").src = "static/images/gear.png";
	else		
		document.getElementById("confBtn").src = "static/images/gear_grey.png";
}

function openConfForm(evt)
{

	if (document.getElementById("confTask").style.display == "block")
		return;

	var node = evt.target || evt.srcElement;					// node clicked in event
	var idx = node.parentNode.rowIndex - 1;						// index of row minus 1 to ignore header row
	var name = String(node.parentNode.childNodes[0].innerText);	// text of first entry of row (task name)
	$.ajax({
		url: "/post",
		type: "post",
		data: "cmd=GET&type=Task&task="+name,
		success: function(data, textStatus, res) {
			data = $.parseJSON(data);
			document.getElementById("e_name").value = name;	
			document.getElementById("e_freq").value = data["freq"];
			document.getElementById("e_cost").value = data["timecost"];
			document.getElementById("e_wt").value = data["weight"];
			document.getElementById("e_last").value = data["last"];
			document.getElementById("e_active").checked = data["isActive"] == "1";
		}
	});

	document.getElementById("confTask").style.display = "block";
}

function closeConfForm()
{
	document.getElementById("e_name").value = "";	
	document.getElementById("e_freq").value = "";
	document.getElementById("e_cost").value = "";
	document.getElementById("e_wt").value = "";
	document.getElementById("e_last").value = "";
	document.getElementById("e_active").checked = false;
	document.getElementById("confTask").style.display = "None";
}

this.setInterval(perUpdate, 3600000); // Update table every hour

function perUpdate()
{
	$.get("/gettasks", function(data, status) {
		constructTable('#table', data);
	});
}
