/**
 * Copyright 2019 IBM Corp. All Rights Reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */


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