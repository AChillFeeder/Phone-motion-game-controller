import React, { useEffect } from 'react';
import { Gyroscope } from 'expo-sensors';

export default function GyroscopeSensor({ onGyroscopeData }) {
  useEffect(() => {
    const subscription = Gyroscope.addListener((data) => {
      onGyroscopeData(data);  // Send the data to App.js through the callback
    });

    Gyroscope.setUpdateInterval(1); // Set update interval to 1000ms (1 second)

    return () => subscription.remove();
  }, []);

  return null;  // This component doesn't render anything, just sends data
}
