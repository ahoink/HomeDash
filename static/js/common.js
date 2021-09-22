function hamburger() {
    var x = document.getElementById("navlinks");
    if (x.style.display == "block") {
        x.style.display = "none";
    }
    else {
        x.style.display = "block";
    }
}

function configureTracker(evt)
{
    window.configureMode = !window.configureMode;
    if (window.configureMode)
        document.getElementById("confBtn").src = "static/images/gear.png";
    else
        document.getElementById("confBtn").src = "static/images/gear_grey.png";

    var tbl = document.getElementById("table");
    for (var i = 1; i < tbl.childElementCount; i++)
    {
        if (window.configureMode)
            tbl.children[i].style.opacity = 0.5;
        else
            tbl.children[i].style.opacity = 1.0;
    }
}

function handleHover(evt)
{
    if (!window.configureMode)
        return;

    var node = evt.target || evt.srcElement;                    // node moused over in event
    if (node.parentElement.nodeName != "TR" || node.parentElement.rowIndex < 1)
        return;
    node.parentElement.style.opacity = 1.0;
}

function handleMouseLeave(evt)
{
    if (!window.configureMode)
        return;

    var node = evt.target || evt.srcElement;                    // node moused over in event
    if (node.parentElement.nodeName != "TR" || node.parentElement.rowIndex < 1)
        return;
    node.parentElement.style.opacity = 0.5;
}
