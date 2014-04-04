require(['config'], function() {
    'use strict';

    require([
            'jquery',
            'modernizr'
    ], function($, ø) {
        // Do stuff.
        console.log('main.js has loaded.');
        console.log('running jQuery version ' + $().jquery + '.');
        console.log('running Modernizr version ' + ø._version + '.');

        // Mappings to handle what happens after
        // success on an AJAX request.
        var successMappings = {
            'bookmark': function(el) {
                var method = el.data('method');
                if (method == 'POST') {
                    el.data('method', 'DELETE');
                    el.find('.action-label').text('Bookmarked');
                    el.addClass('active');

                    el.closest('article').find('.item--bookmark').show();
                } else {
                    el.data('method', 'POST');
                    el.find('.action-label').text('Bookmark');
                    el.removeClass('active');

                    el.closest('article').find('.item--bookmark').hide();
                }
            },

            'watch': function(el) {
                var method = el.data('method');
                if (method == 'POST') {
                    el.data('method', 'DELETE');
                    el.find('.action-label').text('Watching');
                    el.addClass('active');
                } else {
                    el.data('method', 'POST');
                    el.find('.action-label').text('Watch');
                    el.removeClass('active');
                }
            }
        }

        // To handle AJAX links.
        $('a[data-method]').on('click', function(e) {
            e.preventDefault();

            var el      = $(this),
                url     = $(this).attr('href'),
                method  = $(this).data('method'),
                mapping = $(this).data('mapping');

            $.ajax({
                url: url,
                type: method,
                success: function(data, status, xhr) {
                    successMappings[mapping](el);
                },
                error: function(xhr, status, error) {
                    showNotification(xhr.responseText);
                }
            });
        });

        function showNotification(msg) {
            var $notification;

            // Use an existing element if possible.
            if ( $('.popover-notification').length > 0 ) {
                $notification = $('.popover-notification');
                $notification.find('.popover-notification--content').text(msg);

            // Create a new one if needed.
            } else {
                $notification = $('<div class="popover-notification"><div class="popover-notification--content">'+msg+'</div></div>');
                $('body').append($notification);
                $notification.css({
                    bottom: -$notification.outerHeight()
                });
            }

            $notification
                .stop(true)
                .animate({
                    bottom: 0
                })
                .delay(2000)
                .animate({
                    bottom: -$notification.outerHeight()
                });

        }
    });


});
