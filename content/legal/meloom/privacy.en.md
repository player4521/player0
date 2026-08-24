# Meloom Privacy Policy

Effective date: 2026-08-18 (revised 2026-08-18: Android approximate-location only, system backup)

App: Meloom (Android)
Developer: Player Zero
Privacy contact: contact@player0.dev
Published at: https://player0.dev/privacy/ (Korean: https://player0.dev/privacy/ko/)

Meloom shows your real-world location, weather, time and calendar inside a small
virtual room. Meloom has no user accounts and no server of its own. This policy
describes what the app accesses on your device and the one external service it
contacts while you use it.

## Summary

- Meloom has no account system and operates no backend server.
- What you create in the app (your name, your pet, progress, to-dos, settings)
  is kept in the app's own storage on your device and is never uploaded to us.
  Android's own backup and device-transfer features can include that storage.
- The only external network service that Meloom directly contacts is MET Norway,
  for weather and sunrise/sunset times.
- On Android, Meloom asks only for approximate location. It does not request
  precise location.
- Meloom contains no advertising, analytics, crash reporting or tracking SDK.

## Information Meloom accesses

### Location

- Location is optional. Meloom asks for the device location permission only when
  you use a location-based feature, and you can decline.
- On Android, Meloom declares only the approximate location permission
  (ACCESS_COARSE_LOCATION). It does not declare or request the precise location
  permission, so the position the app receives is an approximate one.
- When you allow it, Meloom reads your current position once, at that
  approximate accuracy. If a fresh reading is not available, it may use the last
  known position that the operating system already holds.
- Purpose: to determine your country, to show a place name, and to look up the
  weather for that area. Because the position is approximate, the place name can
  be less exact near a boundary between districts or cities.
- If you decline, or if the device location service is off, the app keeps
  working: you can choose your country manually during onboarding and later in
  Settings, and the app uses that country instead.
- Meloom uses the coordinates for the current lookup only. It does not save your
  latitude and longitude. What it saves is the resulting country code, the place
  name shown on screen, and the time of the lookup.

### Weather (MET Norway)

- To get weather and sunrise/sunset data, Meloom sends the coordinates of that
  approximate position, rounded to four decimal places, to the MET Norway public
  API over HTTPS
  (api.met.no; Locationforecast 2.0 and Sunrise 3.0).
- The request carries a User-Agent header that identifies the app and includes
  the contact address above, as MET Norway's terms require.
- As with any internet request, the IP address of the connection and the
  coordinates contained in the request can appear in MET Norway's own server
  logs and are handled under MET Norway's terms, not by Meloom.
- Meloom sends no name, no account, no device identifier and no advertising
  identifier with these requests.
- Weather data is never used for advertising or profiling.
- MET Norway terms of service: https://api.met.no/doc/TermsOfService

### Turning coordinates into a place name

- On Android and iOS, Meloom asks the operating system's own geocoding service
  to turn the coordinates into a place name and country code.
- That lookup is performed by the platform, not by Meloom. Depending on the
  device, the OS version and the vendor, the platform may resolve it on the
  device or through the vendor's own service, and that handling is governed by
  the OS vendor's privacy policy. Meloom cannot observe which path is used.
- Meloom does not operate or contract any geocoding service of its own.
- On platforms without a native geocoding service, Meloom skips this step and
  uses the coordinates for weather only.

### Calendar

- Calendar access is optional and read-only. Meloom declares only the read
  permission and never asks for permission to write to your calendar.
- When you allow it, Meloom reads the names of your visible calendars and the
  events in the day range it displays (title, start time, end time, all-day
  flag).
- Purpose: to show your schedule for the day inside the room.
- Calendar data is not sent to Meloom or to any other server, and Meloom does
  not save it in app storage. It is held in memory while shown and read again
  from the device the next time it is needed.
- If you decline, the app simply shows no schedule.

### Information stored on your device

Meloom stores the following in the app's own storage on your device
(Android SharedPreferences). None of it is uploaded to us, because there is no
server to upload it to:

- the name you type for yourself and the name you give your pet
- your chosen character, pet type and app settings: country mode, manually
  selected country, display language, learning language, sound settings,
  notification and widget toggles
- app progress: coin balance, wallet, assets, inventory, collection, pet care
  state, reward times, last opened time
- the to-do items you write in the app
- the last successful location result: country code, place name and time
  (not your coordinates)
- the last weather result, together with the country code, place name and how
  the location was obtained (not your coordinates)

This storage is protected by the normal Android application sandbox. Meloom does
not add its own encryption on top of it.

Android provides its own backup and device-transfer features, and an app's
storage can be included in them. Meloom does not turn that off. If the feature is
enabled on your device, a copy of the data listed above can be held by the
operating system's backup or transfer mechanism and restored to a device later.
That copy is created and kept by the operating system and the backup provider
your device uses, under their policies. It does not go to Meloom or to Player
Zero, who keep no server copy of your data.

### Holiday information

Holiday dates ship inside the app as a static data file that is prepared before
release. Looking up a holiday performs no network request and sends nothing
about you anywhere.

## Advertising, analytics and tracking

Meloom contains:

- no advertising SDK and no ads
- no analytics or usage-measurement SDK
- no crash or error reporting SDK
- no third-party behavioural tracking, and no use of an advertising identifier

Meloom does not build a profile of you and does not sell or share your
information with data brokers. If this ever changes, this policy will be updated
before the change ships, and the updated policy will be visible in the app.

## Data retention and deletion

- There is no account, and neither Meloom nor Player Zero keeps a server-side
  copy of your data, so there is nothing for us to retain or delete on our side.
- The app keeps your data on the device until you remove it. On Android you can
  clear it in Settings > Apps > Meloom > Storage > Clear data, or by uninstalling
  the app, which removes the app's storage on that device.
- Clearing or uninstalling does not reach copies held by Android's system backup
  or device-transfer feature. Those copies are kept and removed under the
  policies of the operating system and the backup provider your device uses, and
  they can be restored to a device later.
- Meloom currently has no in-app "delete all my data" button.
- Records held by third parties, such as MET Norway's server logs, are outside
  our control and are retained under that provider's own terms.

## Security

- Requests to MET Norway use HTTPS.
- Meloom operates no backend, holds no accounts and stores no passwords.
- On-device data relies on the Android application sandbox, which keeps other
  apps from reading it on a normal, non-rooted device.

## Third-party services

- MET Norway - weather and sunrise/sunset data. Receives the rounded coordinates
  and, as part of the connection, the IP address.
  https://api.met.no/doc/TermsOfService
- The operating system's geocoding service - turns coordinates into a place
  name, as described above.
- The operating system's backup and device-transfer feature - can include the
  app's on-device storage, as described above. Meloom does not choose the
  provider or hold the resulting copy.
- Google Play distributes the app and applies its own policies to the
  distribution itself.

The holiday data generator (vacanza/holidays) is not a service the app contacts.
It is a build-time tool used to produce the data file bundled with the app.

## Children

Meloom does not ask for your age or date of birth, contains no ads or analytics,
and does not knowingly collect personal information from anyone, including
children. Any name you type is stored only on your device.

## Changes to this policy

If the way Meloom handles information changes, this policy is updated and the
effective date at the top is changed. The policy is bundled with the app, so an
updated policy arrives with an app update.

## Contact

Questions about privacy: contact@player0.dev

This policy is published at https://player0.dev/privacy/ and is also included in
the app.
