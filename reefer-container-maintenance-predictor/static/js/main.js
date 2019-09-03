/*******************************************************************************
 *
 * IBM Confidential
 * OCO Source Materials
 * (C) Copyright IBM Corp. 2015, 2019
 *
 * The source code for this program is not published or otherwise divested of its trade secrets,
 * irrespective of what has been deposited with the U.S. Copyright Office.
 *
 *******************************************************************************/

var lastTimestamp;

function addResultsToTable(results) {
    var resultsTable = document.getElementById("resultsTable");
    for (var i = 0; i < results.length; i++) {
        var res = results[i];
        var row = resultsTable.insertRow(1);
        var cell1 = row.insertCell(0);
        var cell2 = row.insertCell(1);
        var cell3 = row.insertCell(2);
        var cell4 = row.insertCell(3);
        var cell5 = row.insertCell(4);
        var cell6 = row.insertCell(5);

        cell1.innerHTML = (new Date(res.timestamp)).toUTCString();
        cell2.innerHTML = res.id;
        cell3.innerHTML = res.temperature;
        cell4.innerHTML = res.cumulative_power_consumption;
        cell5.innerHTML = res.humidity;
        cell6.innerHTML = res.maintenance_required;
    }
}

function getScoringResults(timestamp) {
    $.ajax({
        url: '/getScoringResult' + (timestamp ? ("?timestamp=" + timestamp) : ""),
        dataType: "json",
        success: function(response) {
            lastTimestamp = response.timestamp;
            if (response.results && response.results.length) {
                addResultsToTable(response.results);
            }
            setTimeout(getScoringResults.bind(null, lastTimestamp), 1000);
        },
        error: function(jqXHR, errorType) {
            console.error("Failed to get scoring result. Error type: " + errorType);
            setTimeout(getScoringResults.bind(null, lastTimestamp), 1000);
        }
    });
}

$(document).ready(function() {
    getScoringResults();
});