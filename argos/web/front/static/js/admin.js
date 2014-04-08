require(['config', 'main'], function() {
    'use strict';

    require([
            'showNotification',
            'filedrop'
    ], function(showNotification) {
        // Do stuff.
        $('.admin-source-icon').each(function() {
            var el = $(this);
            $(this).filedrop({
                url: '/admin/sources/'+$(this).data('id')+'/icon',
                paramname: 'file',
                maxfiles: 1,
                maxfilesize: 1,
                allowedfiletypes: ['image/jpeg','image/png','image/gif'],
                allowedfileextensions: ['.jpg','.jpeg','.png','.gif'],
                uploadFinished: function(i, file, response) {
                    var url = response;
                    el.attr('src', url);
                },
                error: function(err, file) {
                    showNotification(err);
                }
            });
        });
    });


});
