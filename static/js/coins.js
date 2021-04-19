
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
				document.getElementById("cyear").value="";
				document.getElementById("none").checked=true;
				document.getElementById("denver").checked=false;
				document.getElementById("sanfran").checked=false;
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
		}
	});
}
