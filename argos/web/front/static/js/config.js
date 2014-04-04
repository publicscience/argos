requirejs.config({
    baseUrl: '/js',
    paths: {
        jquery: '//ajax.googleapis.com/ajax/libs/jquery/1.10.2/jquery.min',
        modernizr: 'vendor/bower/modernizr/modernizr',
        requirejs: 'vendor/bower/requirejs/require'
    },
    shim: {
        modernizr: {
            exports: 'Modernizr'
        }
        // Example
        //backbone: {
            //deps: ['jquery', 'underscore'],
            //exports: 'Backbone'
        //},
        //underscore: {
            //exports: '_'
        //}
    }
});
