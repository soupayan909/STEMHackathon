'use strict';

/* eslint-enable max-len */

self.addEventListener('install', function(event) {
  console.log('Service Worker installing.');
});

self.addEventListener('activate', function(event) {
  console.log('Service Worker activating.');
});

self.addEventListener('push', function(event) {
  console.log('[Service Worker] Push Received.');
  const pushData = event.data.text();
  console.log(`[Service Worker] Push received this data - "${pushData}"`);
  let data, title, body;
  try {
    data = JSON.parse(pushData);
    title = data.title;
    body = data.body;
  } catch(e) {
    title = "Untitled";
    body = pushData;
  }
  const options = {
    body: "Time for " + body 
  };
  console.log(title, options);

  const promiseChain = self.registration.showNotification(title, options)
  event.waitUntil(
    promiseChain
  );
});

