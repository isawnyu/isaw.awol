// Module: Zotero records

define(function() {
    return {
        name: 'Zotero Record',
        type: 'record',
        toDataUri: function(uri) {
			// alert(uri);
            return uri + '/json';
        },
        corsEnabled: true,
        // add name to data
        parseData: function(data) {

            data.name = data.title;
			// alert(data.title);
            data.latlon = data.reprPoint && data.reprPoint.reverse();
			// alert('inside zotero function'+data.latlon);
			
			//var allItems = new Array();
			/*$.getJSON("http://atripavan.github.io/awld-js/urltozot.json",
				 function(data){
					 $.each(data.items, function(item){
						 //allItems.push(item);
						 console.log(item);
						 alert(item["'"+data.title+"'"]);
					 });
				 });*/			
			
            data.description = 'testing zotero';
			return data;
        }
    };
});
