
function submitCoin()
{
	data = $("#myForm").serialize();
	data = "cmd=ADD&type=Coin&"+data;
	$.ajax({
		url: "/post",
		type: "post",
		data: data,
		success: function(res, textStatus){
			if (res != "\"sall good\"") {
				alert(res);
				document.getElementById("submit_status").innerHTML = "Error Occurred";
			}
			else {
				data = $("#myForm").serializeArray();
				var year = data[0].value;
				var mark = data[1].value;
				if (parseInt(year) < 100) {
					year = (parseInt(year) + 1900).toString();
				}
				document.getElementById("submit_status").innerHTML = "Added " + year + " " + mark;
				document.getElementById("recently_added").innerHTML = year + " " + mark + "\n" + document.getElementById("recently_added").innerHTML
				document.getElementById("cyear").value="";
				document.getElementById("none").checked=true;
				document.getElementById("denver").checked=false;
				document.getElementById("sanfran").checked=false;
			}
		}
	});
	document.getElementById("cyear").focus();
}

function massSubmitCoin()
{
	var num = document.getElementById("massadd").value;
	data = "cmd=ADD&type=Coin&massAdd=" + num;
	$.ajax({
		url: "/post",
		type: "post",
		data: data,
		success: function(res, textStatus){
			if (res != "\"sall good\"") {
				alert(res);
				document.getElementById("submit_status").innerHTML = "Error Occurred";
			}
			else {
				document.getElementById("submit_status").innerHTML = "Mass added " + num + " coins";
				document.getElementById("massadd").value = "";
				document.getElementById("recently_added").innerHTML = num + " undocumented coins";
			}
		}
	});
}

function saveCoinData(evt)
{
	$.ajax({
		url: "/post",
		type: "post",
		data: "cmd=UPDATE&type=Coin",
		success: function(res, textStatus){
			if (res != "\"sall good\"") {
				alert(res);
				document.getElementById("submit_status").innerHTML = "Error Occurred";
			}
			else {
				alert("Saved coin data!");
				//perUpdate();
				document.getElementById("recently_added").innerHTML = "";
			}
		}
	});
}

function undoLast(evt)
{
	$.ajax({
		url: "/post",
		type: "post",
		data: "cmd=UNDO&type=Coin",
		success: function(res, textStatus){
			document.getElementById("submit_status").innerHTML = res;
			var temp = document.getElementById("recently_added").innerHTML;
			var idx = temp.indexOf("\n");
			document.getElementById("recently_added").innerHTML = temp.substring(idx+1, temp.length);
		}
	});
}

function toggleCoinSubmit()
{
	var val = document.getElementById("coinToggle").checked;
	if (val)
	{
		document.getElementsByClassName("indivCoinSubmit")[0].style.display = "none";
		document.getElementsByClassName("massCoinSubmit")[0].style.display = "block";
	}
	else
	{
		document.getElementsByClassName("indivCoinSubmit")[0].style.display = "block";
		document.getElementsByClassName("massCoinSubmit")[0].style.display = "none";
	}
}
