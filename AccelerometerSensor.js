import React, { useEffect } from 'react';
import { Accelerometer } from 'expo-sensors';

export default function AccelerometerSensor({ onAccelerometerData }) {
  useEffect(() => {
    const subscription = Accelerometer.addListener((data) => {
      onAccelerometerData(data);  // Send the data to App.js through the callback
    });

    Accelerometer.setUpdateInterval(10); // Set update interval to 1000ms (1 second)

    return () => subscription.remove();
  }, []);

  return null;  // This component doesn't render anything, just sends data
}
