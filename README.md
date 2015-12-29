An alternative implementation of OTA server for CM ROMs used in my i9082 unofficial CM.

It's not really designed to be flexible and easily re-usable, but if you need
an OTA server implementation for your unofficial CM build, feel free to fork,
modify and use it as you need.

To point a CM ROM to an alternative update server, add the following build
property:

    cm.updater.uri=https://your-server/api
