// Dynamically create table with rows and columns based on data passed in
function constructTable(selector, data)
{
	var hdrs = data["Headers"]
	var plants = data["Plants"]
	$('#table tr').remove();            // remove table if it already exists
	var cols = Headers(hdrs, selector); // extract columns from headers
	for (var i = 0; i < plants.length; i++)
	{
		var row = $('<tr/>');
		for (var colIdx = 0; colIdx < cols.length; colIdx++)
		{
			var val = plants[i][cols[colIdx]];
			if (val == null) val = "";
				row.append($('<td/>').html(val));
		}

		// Set row color to color passed from python backend
		row[0].style.backgroundColor=plants[i]["Color"]
		$(selector).append(row);
	}
}

// Columns based on number of headers (number of elements in each plant entry)
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
	var idx = node.parentNode.rowIndex - 1;                     // index of row minus 1 to ignore header row
	var name = String(node.parentNode.childNodes[0].innerText); // text of first entry of row (plant name)
	$.ajax({
		url: "/post",
		type: "post",
		data: "cmd=UPDATE&type=Plant&plant="+name,
		success: function(data, textStatus, res) {
			data = $.parseJSON(data);
			node.parentNode.childNodes[1].innerText=data[0];    // re-set last watered date
			node.parentElement.style.backgroundColor="#80FF80"; // reset row color to green
			document.getElementById("loader").style.display="none"; // turn off loading spinner
		}
	});
}

function submitNewPlant()
{
	//e.preventDefault();
	data = $("#myForm").serialize(); // data entered by user
	data = "cmd=ADD&type=Plant&"+data
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
				alert("Successfully added plant");
				document.getElementById("pname").value="";
				perUpdate();
			}
		}
	});
}

function undoLastAction(evt)
{
	$.ajax({
		url: "/post",
		type: "post",
		data: "cmd=UNDO&type=Plant",
		success: function(){
			alert("Undo successful - Reverted to previous state");
			perUpdate();
		}
	});
}

this.setInterval(perUpdate, 3600000) // Update table every hour

function perUpdate()
{
	$.get("/getplants", function(data, status) {
		constructTable('#table', data);
	});
}
