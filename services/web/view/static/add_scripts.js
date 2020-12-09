function getPredictPeriod(timeline) {
    //console.log(timeline.itemsData)
    var data = Object.values(timeline.itemsData._data).reduce((acc, item) => {
					
        if (item['content'] == 'Predict period') {
            acc['start'] = item['start']
            acc['end'] = item['end']
        }
        return acc
    }, {})

    return data
}

function createTimeline(container) {
    var items = [
        {start: new Date(2021, 2, 1), 
        end: new Date(2021, 2, 28), 
        content: 'Predict period'}
    ];
    
    // create visualization
    
    var options = {
        height: '120px',
        min: new Date(2020, 11, 28),                // lower limit of visible range
        max: new Date(2021, 3, 1),                // upper limit of visible range
        zoomMin: 1000 * 60 * 60 * 24,             // one day in milliseconds
        zoomMax: 1000 * 60 * 60 * 24 * 31 * 3,     // about three months in milliseconds
        editable: { 
            remove: false, 
            updateTime: true
        },
        clickToUse: true,
        onUpdate: function(item, callback){
             console.log(item)
             callback(item)
        }
    };

    // create the timeline
    var timeline = new vis.Timeline(container);

    $.ajax({
        url: "/view/get_time_ranges",
        method: "GET",
        success: function (data) {
            options['min'] = new Date(Date.parse(data['start_b']))
            options['max'] = new Date(Date.parse(data['end_b']))
            options['zoomMax'] = Date.parse(data['end_b']) - Date.parse(data['start_b'])
            
            items[0]['start'] = new Date(Date.parse(data['start']))
            items[0]['end'] = new Date(Date.parse(data['end']))
            timeline.setOptions(options);
            timeline.setItems(new vis.DataSet(items));
        }
    })

    return timeline
}

function addLegend(svg, width) {
    var legend_keys = ["arma", "boosting", "linear"]
    var color_scale = {
        "arma": "red",
        "boosting": "purple",
        "linear": "orange"
    }

    var lineLegend = svg.selectAll(".lineLegend").data(legend_keys)
        .enter().append("g")
        .attr("class","lineLegend")
        .attr("transform", function (d,i) {
                return "translate(" + (width + 10) + "," + (i*20)+")";
            });

    lineLegend.append("text").text(function (d) {return d;})
        .attr("transform", "translate(15,9)"); //align texts with boxes

    lineLegend.append("rect")
        .attr("fill", function (d, i) { return color_scale[d] })
        .attr("width", 10).attr("height", 10);
}