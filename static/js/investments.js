
function constructTable(selector, data)
{
	var hdrs = data["Headers"];
	var assets = data["Investments"];

	$('#table tr').remove();
	
	var cols = Headers(hdrs, selector);
	for (var i = 0; i < assets.length; i++)
	{
		var row = $('<tr/>');
		for (var colIdx = 0; colIdx < cols.length; colIdx++)
		{
			var val = assets[i][cols[colIdx]];
			if (val == null) val = "";
				row.append($('<td/>').html(val));
		}

		row[0].style.backgroundColor=assets[i]["Color"]
		if (i == assets.length - 1)
			row[0].style.fontWeight = "bold";
		$(selector).append(row);
	}
}

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

function handleClick(evt)
{
	if (window.configureMode) {
		openConfForm(evt);
	}
	else {
		var node = evt.target || evt.srcElement;
		var name = String(node.parentNode.childNodes[0].innerText);
		var amount = null;
		/*$.ajax({
			url: "/post",
			type: "post",
			data: "cmd=UPDATE&type=Expense&exp="+name+"&amount="+amount,
			success: function(data, textStatus, res) {
				data = $.parseJSON(data);
				node.parentNode.childNodes[1].innerText="$" + data[1]; // amount
				node.parentNode.childNodes[2].innerText=data[0]; // due date
				node.parentElement.style.backgroundColor="#80FF80";
			}
		});*/
	}
}

function submitNewInvest()
{
	data = $("#myForm").serialize();
	data = "cmd=ADD&type=Investment&"+data;
	$.ajax({
		url: "/post",
		type: "post",
		data: data,
		success: function(res, textStatus){
			if (res != "\"sall good\"") {
				alert(res)
			}
			else {
				alert("Successfully added Investment");
				document.getElementById("name").value="";
				document.getElementById("sym").value="";
				document.getElementById("qnt").value="";
				document.getElementById("amt").value="";
				perUpdate();
			}
		}
	});
}

function editInvestment()
{
	data = $("#confInvForm").serialize();
	data = "cmd=EDIT&type=Investment&"+data;
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
					alert("Successfully modified investment");
				}
			}
	});
}

function openConfForm(evt)
{
	if (document.getElementById("confInvest").style.display == "block")
		return;

	var node = evt.target || evt.srcElement;
	var idx = node.parentNode.rowIndex - 1;
	var name = String(node.parentNode.childNodes[0].innerText);

	$.ajax({
			url: "/post",
			type: "post",
			data: "cmd=GET&type=Investment&inv="+name,
			success: function(data, textStatus, res){
				data = $.parseJSON(data);
				document.getElementById("i_name").value = name;
				document.getElementById("i_amt").value = data["cost"];
				document.getElementById("i_qnt").value = data["quantity"];
				document.getElementById("i_type").value = data["type"];
			}
	});

	document.getElementById("confInvest").style.display = "block";

}

function closeConfForm()
{
	document.getElementById("i_name").value = "";
	document.getElementById("i_amt").value = "";
	document.getElementById("i_qnt").value = "";
	document.getElementById("i_type").value = "";
	document.getElementById("confInvest").style.display = "None";
}

function undoLastAction(evt)
{
	$.ajax({
		url: "/post",
		type: "post",
		data: "cmd=UNDO&type=Investment",
		success: function(){
			perUpdate();
		}
	});
}

this.setInterval(perUpdate, 3600000)

function perUpdate()
{
	$.get("/getinv", function(data, status) {
		constructTable('#table', data)
	});
}
