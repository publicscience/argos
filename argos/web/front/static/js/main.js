require(['config'], function() {
    'use strict';

    require([
            'jquery',
            'modernizr',
            'showNotification'
    ], function($, ø, showNotification) {
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

                    el.closest('article').find('.bookmark-flag').show();
                } else {
                    el.data('method', 'POST');
                    el.find('.action-label').text('Bookmark');
                    el.removeClass('active');

                    el.closest('article').find('.bookmark-flag').hide();
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

        // For handling AJAX links.
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

        var moreMappings = {
            'articles': function(el, data) {
                var articles = $(data).find('.articles ul').html()
                el.closest('.articles').find('ul').html(articles);
            }
        }

        // For handling "more" buttons.
        $('.js-more').on('click', function() {
            var el      = $(this),
                url     = $(this).data('href'),
                mapping = $(this).data('mapping');

            $.ajax({
                url: url,
                type: 'GET',
                success: function(data, status, xhr) {
                    moreMappings[mapping](el, data);
                },
                error: function(xhr, status, error) {
                    showNotification(xhr.responseText);
                }
            });
        });

    });

});

define('showNotification', ['jquery'], function($) {
    return function(msg) {
        var $notification;

        // Use an existing element if possible.
        if ( $('.popover-notification').length > 0 ) {
            $notification = $('.popover-notification');
            $notification.find('.popover-notification-content').text(msg);

        // Create a new one if needed.
        } else {
            $notification = $('<div class="popover-notification"><div class="popover-notification-content">'+msg+'</div></div>');
            $('body').append($notification);
            $notification.css({
                bottom: -$notification.outerHeight()
            });
        }

        $notification
            .stop(true)
            .animate({
                bottom: 0,
                opacity: 1
            })
            .delay(2000)
            .animate({
                bottom: -$notification.outerHeight(),
                opacity: 0
            });
    }
});
