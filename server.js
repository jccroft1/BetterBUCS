var express = require('express');
var app = express();
var fs = require("fs");
var sqlite3 = require("sqlite3").verbose();

var dbName = "bucsLive.db";
var db = new sqlite3.Database(dbName);


app.get('/teams', function (req, res) {

  db.serialize(function() {

    db.all("SELECT * FROM teams WHERE university = 'Lancaster University'", function(err, teams) {

      res.json(teams);
    });
  });
});



var server = app.listen(8081, function () {

  var host = server.address().address
  var port = server.address().port

  console.log("Example app listening at http://%s:%s", host, port)

});
