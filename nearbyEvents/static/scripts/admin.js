"use strict";
// This admin.js is adapted from the example by https://lovelace.oulu.fi/ohjelmoitava-web/ohjelmoitava-web/
// fit to our application
const DEBUG = true;
const MASONJSON = "application/vnd.mason+json";
const PLAINJSON = "application/json";

function renderError(jqxhr) {
    let msg = jqxhr.responseJSON["@error"]["@message"];
    $("div.notification").html("<p class='error'>" + msg + "</p>");
}

function renderMsg(msg) {
    $("div.notification").html("<p class='msg'>" + msg + "</p>");
}

function getResource(href, renderer) {
    $.ajax({
        url: href,
        success: renderer,
        error: renderError
    });
}

function sendData(href, method, item, postProcessor) {
    $.ajax({
        url: href,
        type: method,
        data: JSON.stringify(item),
        contentType: PLAINJSON,
        processData: false,
        success: postProcessor,
        error: renderError
    });
}

function deleteData(href, method, postProcessor) {
    $.ajax({
        url: href,
        type: method,
        processData: false,
        success: postProcessor,
        error: renderError
    });
}

function areaRow(item) {
    let link = "<a href='" +
                item["@controls"].self.href +
                "' onClick='followLink(event, this, renderArea)'>show</a>";

    return "<tr><td>" + item.name +
            "</td><td>" + link + "</td></tr>";
}

function eventRow(item) {
    let link = "<a href='" +
                item["@controls"].self.href +
                "' onClick='followLink(event, this, renderEvent)'>show</a>" +
				" | <a href='";
	if (typeof item["@controls"]["nearby:area"] !== 'undefined') {
		link = link+item["@controls"]["nearby:area"].href +
                "' onClick='followLink(event, this, renderArea)'>area</a>"
				;
	}

    return "<tr><td>" + item.name +
            "</td><td>" + link + "</td></tr>";
}

function eventAreaRow(item) {
    let link = "<a href='" +
                item["@controls"].self.href +
                "' onClick='followLink(event, this, renderEvent)'>show event</a>" +
				" | <a href='";
	//if (typeof item["@controls"]["nearby:area"] !== 'undefined') {
	//	link = link+item["@controls"]["nearby:area"].href +
    //            "' onClick='followLink(event, this, renderArea)'>show area</a>"
	//			;
	//}

    return "<tr><td>" + item.name + " in area: " + "<a href='" +
                item["@controls"]["nearby:area"].href +
                "' onClick='followLink(event, this, renderArea)'>" + item.area_name + "</a>" +
            "</td><td>" + link + "</td></tr>";
}

function appendAreaRow(body) {
    $(".resulttable tbody").append(areaRow(body));
}

function appendEventRow(body) {
    $(".resulttable tbody").append(eventRow(body));
}

function appendEvenAreatRow(body) {
    $(".resulttable tbody").append(eventAreaRow(body));
}

function getDeletedArea(data, status, jqxhr) {
    renderMsg("Deleted");
	$(".resulttable thead").empty();
	$(".resulttable tbody").empty();
	$("div.tablecontrols").empty();
}

function getDeletedEvent(data, status, jqxhr) {
    renderMsg("Deleted");
	$(".resulttable thead").empty();
	$(".resulttable tbody").empty();
	$("div.tablecontrols").empty();
}

function getSubmittedArea(data, status, jqxhr) {
    renderMsg("Successful");
    let href = jqxhr.getResponseHeader("Location");
    if (href) {
        getResource(href, appendAreaRow);
    }
}

function getSubmittedEvent(data, status, jqxhr) {
    renderMsg("Successful");
    let href = jqxhr.getResponseHeader("Location");
    if (href) {
        getResource(href, appendEventRow);
    }
}

function followLink(event, a, renderer) {
    event.preventDefault();
    getResource($(a).attr("href"), renderer);
}

function submitArea(event) {
    event.preventDefault();

    let data = {};
    let form = $("div.form form");
    data.name = $("input[name='name']").val();
    sendData(form.attr("action"), form.attr("method"), data, getSubmittedArea);
}

function submitEvent(event) {
    event.preventDefault();

    let data = {};
    let form = $("div.form form");
    data.name = $("input[name='name']").val();
	data.status = $("input[name='status']").val();
	data.event_begin = $("input[name='event_begin']").val();
	data.area_name = $("input[name='area_name']").val();
	data.max_tickets = 99;
	data.ticket_price = 0;
    sendData(form.attr("action"), form.attr("method"), data, getSubmittedEvent);
}

function renderAreaCollectionForm(ctrl) {
    let form = $("<form>");
    let name = ctrl.schema.properties.name;
    form.attr("action", ctrl.href);
    form.attr("method", ctrl.method);
    form.submit(submitArea);
    form.append("<label>" + ctrl.title + "</label>");
    form.append("<input type='text' name='name'>");
    ctrl.schema.required.forEach(function (property) {
        $("input[name='" + property + "']").attr("required", true);
    });
    form.append("<input type='submit' name='submit' value='Submit'>");
    $("div.form").html(form);
}

function renderEventCollectionForm(ctrl) {
    let form = $("<form>");
    let name = ctrl.schema.properties.name;
    form.attr("action", ctrl.href);
    form.attr("method", ctrl.method);
    form.submit(submitEvent);
    form.append("<label>" + ctrl.title + "</label>");
    form.append("<input type='text' name='name'>");
	form.append("<label> Status </label>");
    form.append("<input type='text' name='status'>");
	form.append("<label>When will it start</label>");
    form.append("<input type='text' name='event_begin'>");
	form.append("<label>In which area it is</label>");
    form.append("<input type='text' name='area_name'>");
    ctrl.schema.required.forEach(function (property) {
        $("input[name='" + property + "']").attr("required", true);
    });
    form.append("<input type='submit' name='submit' value='Submit'>");
    $("div.form").html(form);
}


function renderAreaForm(ctrl) {
    let button = $("<button>");
    let name = ctrl.title;
	button.html("Delete area");
	button.attr("onClick", "deleteData('"+ctrl.href+"', '"+ctrl.method+"', getDeletedArea)")
    //$("div.form").html(button);
	$(".resulttable tbody").append(button);
}

function renderArea(body) {
    $("div.navigation").html(
        "<a href='" +
        body["@controls"].collection.href +
        "' onClick='followLink(event, this, renderAreas)'>Areas</a>" +
		" | " + "<a href='" +
        body["@controls"]["nearby:events-by"].href +
        "' onClick='followLink(event, this, renderEventsByArea)'>Look for events</a>"
    );
    $(".resulttable thead").empty();
	$(".resulttable thead").append(body.name);
    $(".resulttable tbody").empty();
    renderAreaForm(body["@controls"]["nearby:delete-area"]);
	renderAreaCollectionForm(body["@controls"]["nearby:edit-area"]);
}

function renderEventForm(ctrl) {
    let button = $("<button>");
    let name = ctrl.title;
	button.html("Delete event");
	button.attr("onClick", "deleteData('"+ctrl.href+"', '"+ctrl.method+"', getDeletedEvent)")
    //$("div.form").html(button);
	$(".resulttable tbody").append(button);
}

function renderEvent(body) {
    $("div.navigation").html(
        "<a href='" +
        body["@controls"].collection.href +
        "' onClick='followLink(event, this, renderEvents)'>Events</a>" 
    );
    $(".resulttable thead").empty();
	$(".resulttable thead").append(body.name);
    $(".resulttable tbody").empty();
    renderEventForm(body["@controls"]["nearby:delete-event"]);
	renderEventCollectionForm(body["@controls"]["nearby:edit-event"]);
}

function renderAreas(body) {
    $("div.navigation").empty();
    $("div.tablecontrols").empty();
    $(".resulttable thead").html(
        "<tr><th>Name</th><th>Actions</th></tr>"
    );
    let tbody = $(".resulttable tbody");
    tbody.empty();
    body.items.forEach(function (item) {
        tbody.append(areaRow(item));
    });
    renderAreaCollectionForm(body["@controls"]["nearby:add-area"]);
}

function renderEvents(body) {
    $("div.navigation").empty();
    $("div.tablecontrols").empty();
    $(".resulttable thead").html(
        "<tr><th>Name</th><th>Actions</th></tr>Location</th></tr>"
    );
    let tbody = $(".resulttable tbody");
    tbody.empty();
    body.items.forEach(function (item) {
        tbody.append(eventRow(item));
    });
    renderEventCollectionForm(body["@controls"]["nearby:add-event"]);
}

function renderEventsByArea(body) {
    $("div.navigation").empty();
    $("div.tablecontrols").empty();
	$("div.form").empty();
	$("div.navigation").html(
        "<a href='" +
        body["@controls"]["nearby:areas-collection"].href +
        "' onClick='followLink(event, this, renderAreas)'>Areas</a>"
    );
    $(".resulttable thead").html(
        "<tr><th>Event Name</th><th>Actions</th></tr>"
    );
    let tbody = $(".resulttable tbody");
    tbody.empty();
    body.items.forEach(function (item) {
        tbody.append(eventAreaRow(item));
    });
}

$(document).ready(function () {
    getResource("http://localhost:5000/api/areas/", renderAreas);
});
