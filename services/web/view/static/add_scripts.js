function getPredictPeriod(timeline) {
    var data = Object.values(timeline.itemsData).reduce((acc, item) => {
					
        if (item['content'] == 'Predict period') {
            acc['start'] = item['start']
            acc['end'] = item['end']
        }
        return acc
    }, {})

    return data
}