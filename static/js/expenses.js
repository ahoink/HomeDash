
function displayStats() {
	for (var t in stats) {
		txt.innerHTML = txt.innerHTML + "\n\t<u>" + t + "</u>: ";
		txt.innerHTML = txt.innerHTML + "$" + stats[t]["min"].toFixed(2) + " - $" + stats[t]["max"];
		txt.innerHTML = txt.innerHTML + " ($" + stats[t]["avg"] + ")\n\n";
	}
}                                                                                                                               

function constructTable(selector, data)
{
	var hdrs = data["Headers"];
	var exps = data["Expenses"];
	var autovar = data["Auto-vari"];
	$('#table tr').remove();
	var cols = Headers(hdrs, selector);
	for (var i = 0; i < exps.length; i++)
	{
		var row = $('<tr/>');
		for (var colIdx = 0; colIdx < cols.length; colIdx++)
		{
			var val = exps[i][cols[colIdx]];
			if (val == null) val = "";
				row.append($('<td/>').html(val));
		}

		row[0].style.backgroundColor=exps[i]["Color"]
		row[0].tabIndex=exps[i]["isVar"]                // use tabIndex attribute as boolean for whether or not the expense is variable
		$(selector).append(row);
	}

	for (var i = 0; i < autovar.length; i++)
	{
		var name = autovar[i];
		amount = prompt("Variable expense '" + name + "' has autopay enabled and is past due. Enter the amount paid", "");
		if (amount == null) continue;
		$.ajax({
			url: "/post",
			type: "post",
			data: "cmd=UPDATE&type=Expense&exp="+name+"&amount="+amount,
			success: function(data, textStatus, res) {
				perUpdate();
			}
		});
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
		var idx = node.parentNode.rowIndex - 1;
		var name = String(node.parentNode.childNodes[0].innerText);
		var amount = null;
		if (node.parentNode.tabIndex == 1) {
			amount = prompt("Enter the amount", "");
			if (amount == null) return;
		}
		$.ajax({
			url: "/post",
			type: "post",
			data: "cmd=UPDATE&type=Expense&exp="+name+"&amount="+amount,
			success: function(data, textStatus, res) {
				data = $.parseJSON(data);
				node.parentNode.childNodes[1].innerText="$" + data[1]; // amount
				node.parentNode.childNodes[2].innerText=data[0]; // due date
				node.parentElement.style.backgroundColor="#80FF80";
			}
		});
	}
}

function submitNewExp()
{
	//e.preventDefault();
	data = $("#myForm").serialize();
	data = "cmd=ADD&type=Expense&"+data;
	$.ajax({
		url: "/post",
		type: "post",
		data: data,
		success: function(res, textStatus){
			if (res != "\"sall good\"") {
				alert(res)
			}
			else {
				alert("Successfully added Expense");
				document.getElementById("name").value="";
				document.getElementById("amt").value="";
				document.getElementById("due").value="";
				document.getElementById("autopay").checked=false;
				document.getElementById("isvar").checked=false;
				perUpdate();
			}
		}
	});
}

function editExpense()
{
	data = $("#confExpForm").serialize();
	data = "cmd=EDIT&type=Expense&"+data;
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
					alert("Successfully modified expense");
				}
			}
	});
}

function openConfForm(evt)
{
	if (document.getElementById("confExpense").style.display == "block")
		return;

	var node = evt.target || evt.srcElement;
	var idx = node.parentNode.rowIndex - 1;
	var name = String(node.parentNode.childNodes[0].innerText);

	$.ajax({
			url: "/post",
			type: "post",
			data: "cmd=GET&type=Expense&exp="+name,
			success: function(data, textStatus, res){
				data = $.parseJSON(data);
				document.getElementById("e_name").value = name;
				document.getElementById("e_amt").value = data["amount"];
				document.getElementById("e_due").value = data["due"];
				document.getElementById("e_auto").checked = data["autopay"];
				document.getElementById("e_vari").checked = data["variable"];
			}
	});

	document.getElementById("confExpense").style.display = "block";

}

function closeConfForm()
{
	document.getElementById("e_name").value = "";
	document.getElementById("e_amt").value = "";
	document.getElementById("e_due").value = "";
	document.getElementById("e_auto").checked = false;
	document.getElementById("e_vari").checked = false;
	document.getElementById("confExpense").style.display = "None";
}

function undoLastAction(evt)
{
	$.ajax({
		url: "/post",
		type: "post",
		data: "cmd=UNDO&type=Expense",
		success: function(){
			perUpdate();
		}
	});
}

this.setInterval(perUpdate, 3600000)

function perUpdate()
{
	$.get("/getexp", function(data, status) {
		constructTable('#table', data)
	});
}
