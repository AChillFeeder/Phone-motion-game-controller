
<!-- python Desktop\PhoneGameController\main.py -->

<!-- adb connect 192.168.1.191:42039
cd Desktop\PhoneGameController

npx react-native run-android -->

---

# Install the app

> In motion UDP

```bash
./gradlew clean
./gradlew assembleDebug
adb connect 192.168.1.191:37137
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

# Launch the server
```bash
python .\server\java_server.py
```

---

Reintroduce direction-based filtering (e.g., upward-only attacks),
Add rotation-based parries,
Or support custom patterns (e.g., combos, chaining).


