"use strict";

angular.module("seccamApp", ["ngAnimate", "ngAria", "ngCookies", "ngMessages", "ngResource", "ngRoute", "ngSanitize", "ngTouch"])
  .config(["$routeProvider", function(a) {
    a.when("/", {
        templateUrl: "views/main.html",
        controller: "MainCtrl",
        controllerAs: "main"
      })
      .when("/live-stream", {
        templateUrl: "views/live-stream.html",
        controller: "LiveStreamCtrl"
      })
      .when("/photos", {
        templateUrl: "views/photos.html",
        controller: "PhotosCtrl"
      })
      .otherwise({
        redirectTo: "/"
      })
  }])
  .controller("BaseController", ["$scope", "$location", function(a, b) {
    a.isActive = function(a) {
      return a === b.url()
    }
  }]), angular.module("seccamApp")
  .controller("MainCtrl", function() {
    this.awesomeThings = ["HTML5 Boilerplate", "AngularJS", "Karma"]
  }), angular.module("seccamApp")
  .controller("LiveStreamCtrl", ["$scope", function(a) {
    a.isChrome = !!window.chrome;
    a.streamStarted = !1;
    var b = "http://" + window.location.hostname + ":81/video.cgi";
    a.startStream = function() {
      a.streamStarted || (a.streamStarted = !0, $("#video-stream")
        .attr("src", b))
    }
  }]), angular.module("seccamApp")
  .controller("PhotosCtrl", ["$scope", "$http", "$interval", function(a, b, c) {
    a.photos = [];
    var d = "/photos",
      e = 6e4,
      f = null,
      g = function() {
        b.get(d)
          .then(function(b) {
            a.photos = b.data
          })
      };
    g(), f = c(g, e)
  }]), angular.module("seccamApp");
