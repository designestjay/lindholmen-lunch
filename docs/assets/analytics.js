/* Cookieless analytics.
   No request is sent until data-endpoint is an https URL.
   [CONFIRM: analytics processor] — Plausible, Umami, or GoatCounter, EU-hosted.
   This file does not set cookies or write localStorage. */
(function () {
    var script = document.currentScript;
    var endpoint = ((script && script.dataset && script.dataset.endpoint) || "").trim();
    var enabled = endpoint.indexOf("https://") === 0 && endpoint.indexOf("CONFIRM") === -1;
    var src = "";
    try {
        src = new URLSearchParams(window.location.search).get("src") || "";
    } catch (err) {
        src = "";
    }
    var queue = [];

    function track(name, props) {
        var event = {
            name: name,
            props: props || {},
            t: Date.now()
        };
        if (src) event.src = src;
        queue.push(event);
        if (!enabled) return;
        try {
            var body = JSON.stringify(event);
            if (navigator.sendBeacon) {
                navigator.sendBeacon(endpoint, new Blob([body], { type: "application/json" }));
            }
        } catch (err) {}
    }

    window.lunchTrack = track;
    window.lunchEvents = queue;
})();
