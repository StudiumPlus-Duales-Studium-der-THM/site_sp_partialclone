(function($, window, document, undefined) {
    "use strict";

    jQuery( document ).ready(function($) {
        setTimeout(function () {
            $('select[data-filter="dropdown"]').each(function() {
                // Cache the current select element
                var $select = $(this);

                if($(this).data('name') == 'category'){
                    return true;
                }

                // Get all options except the first one
                var $options = $select.find('option').not(':first');

                // Convert options to an array of their text values for sorting
                var optionsArray = $options.map(function() {
                    return $(this).text();
                }).get();

                // Sort options array
                optionsArray.sort(function(a, b) {
                    var nameA = a.toUpperCase();
                    var nameB = b.toUpperCase();
                    if (nameA < nameB) return -1;
                    if (nameA > nameB) return 1;
                    return 0;
                });

                // Empty the select except for the first option
                $select.find('option').not(':first').remove();

                // Append sorted options back to the select element
                $.each(optionsArray, function(index, text) {
                    $select.append($('<option></option>').text(text).val(text.toLowerCase()));
                });
            });
        },300);

        jQuery.fn.dmsmp_marker_html = function ( options ) { 
            
        
        
    
          let map_obj = jQuery(options.wpgmp_map_selector).data("wpgmp_maps");
         
            map_obj.addon_create_marker= function() {


                var map_obj = this;
                $('select[data-filter="dropdown"]').each(function() {
                    // Cache the current select element
                    var $select = $(this);

                    // Get all options except the first one
                    var $options = $select.find('option').not(':first');

                    // Convert options to an array of their text values for sorting
                    var optionsArray = $options.map(function() {
                        return $(this).text();
                    }).get();

                    // Sort options array
                    optionsArray.sort(function(a, b) {
                        var nameA = a.toUpperCase();
                        var nameB = b.toUpperCase();
                        if (nameA < nameB) return -1;
                        if (nameA > nameB) return 1;
                        return 0;
                    });

                    // Empty the select except for the first option
                    $select.find('option').not(':first').remove();

                    // Append sorted options back to the select element
                    $.each(optionsArray, function(index, text) {
                        $select.append($('<option></option>').text(text).val(text));
                    });
                });
                   
            
            }
            // map_obj.addon_create_marker();
        
    },

    jQuery("div.wpgmp_map_container").each(function (index, element) {
        var container = $(element); // Cache the current container element

        setTimeout(function () {
            container.find(".wpgmp_map").each(function () {
                var mapElement = $(this);
                var mapId = mapElement.data("map-id");
                var mapVarName = "mapdata" + mapId;
                var mapData = window.wpgmp && window.wpgmp[mapVarName];

                if (mapData) {
                    $("#map" + mapId).maps(mapData).data("wpgmp_maps");
                } else {
                    console.warn("Map data missing for map: " + mapId);
                }
            });

        }, 200);
    });
    // setTimeout(function () {
    //     jQuery("div.wpgmp_map_container").each(function (index, element) { 
            
    //             let wpgmp_map_selector = "#"+$(this).attr('rel');
    //             setTimeout(function () {
    //             let wpgmp_layout_args = {'wpgmp_map_selector' : wpgmp_map_selector};
    //                 // jQuery(wpgmp_map_selector).dmsmp_marker_html(wpgmp_layout_args);
    //             }, 500);
            
    //     });
    // }, 400);

});
}(jQuery, window, document));