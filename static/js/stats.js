function displayStats()
{
	for (var t in stats)
	{
		txt.innerHTML = txt.innerHTML + "\n\t<u>" + t + "</u>\n";
		txt.innerHTML = txt.innerHTML + "\t\tAverage Score: " + stats[t]["avgscore"].toFixed(2) + nl;
		txt.innerHTML = txt.innerHTML + "\t\tMost Frequent Day: " + stats[t]["day"] + nl;
		txt.innerHTML = txt.innerHTML + "\t\tAverage Frequency: " + stats[t]["freq"] + nl + nl;
	}
}

// Dynamically create table with rows and columns based on data passed in
function constructTable(selector, data)
{
	var hdrs = data["Headers"]
	var tasks = data["Stats"]
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
		//row[0].style.backgroundColor=tasks[i]["Color"]
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
	//document.getElementById("loader").style.display="block";

	var node = evt.target || evt.srcElement;                    // node clicked in event
	var idx = node.cellIndex                      // index of row minus 1 to ignore header row
	//var name = String(node.parentNode.childNodes[0].innerText)  // text of first entry of row (task name)
	$.ajax({
		url: "/post",
		type: "post",
		data: "cmd=UPDATE&type=Stats&sort_col="+idx,
		success: function(data, textStatus, res) {
			data = $.parseJSON(data);
			constructTable('#table', data);
			//node.parentNode.childNodes[1].innerText=data[0]     // re-set last completed date
			//node.parentNode.childNodes[2].innerText=data[1]     // re-set due time
			//node.parentElement.style.backgroundColor="#80FF80"  // reset row color to green
			//document.getElementById("loader").style.display="none"; // turn off loading spinner
		}
	});
}
