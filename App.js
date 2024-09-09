import React, { useEffect, useState, useRef } from 'react';
import { View, Text } from 'react-native';
import { Gyroscope, Accelerometer, DeviceMotion } from 'expo-sensors';

export default function App() {
  const [isWsOpen, setIsWsOpen] = useState(false);  // WebSocket connection status
  const ws = useRef(null);  // WebSocket reference
  const gyroscopeDataRef = useRef({ x: 0, y: 0, z: 0 });  // Gyroscope data reference
  const accelerometerDataRef = useRef({ x: 0, y: 0, z: 0 });  // Accelerometer data reference

  // Initialize WebSocket connection
  useEffect(() => {
    ws.current = new WebSocket('ws://192.168.1.181:6790');  // Replace with your server's IP and port

    ws.current.onopen = () => {
      setIsWsOpen(true);
      console.log('WebSocket connection is open');
    };

    ws.current.onclose = () => {
      setIsWsOpen(false);
      console.log('WebSocket connection closed');
    };

    ws.current.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    return () => {
      if (ws.current && ws.current.readyState === WebSocket.OPEN) {
        console.log('Closing WebSocket before unmount');
        ws.current.close();
      }
    };
  }, []);

  // Gyroscope data collection
  useEffect(() => {
    const gyroscopeSubscription = Gyroscope.addListener((data) => {
      gyroscopeDataRef.current = data;  // Update the reference directly
      console.log('Gyroscope data:', data);
    });

    Gyroscope.setUpdateInterval(1);  // Update every 1ms

    return () => gyroscopeSubscription && gyroscopeSubscription.remove();
  }, []);

  // Accelerometer data collection
  useEffect(() => {
    const accelerometerSubscription = Accelerometer.addListener((data) => {
      accelerometerDataRef.current = data;  // Update the reference directly
      console.log('Accelerometer data:', data);
    });

    Accelerometer.setUpdateInterval(1);  // Update every 1ms

    return () => accelerometerSubscription && accelerometerSubscription.remove();
  }, []);

  // Send sensor data to WebSocket every second
  useEffect(() => {

    const interval = setInterval(() => {
      if (isWsOpen && ws.current && ws.current.readyState === WebSocket.OPEN) {
        const sensorData = {
          gyroscope: gyroscopeDataRef.current,  // Access the latest data from the refs
          accelerometer: accelerometerDataRef.current,
        };
        console.log('Sending data:', sensorData);
        ws.current.send(JSON.stringify(sensorData));  // Send the sensor data
      }
    }, 1);  // Send data every second

    return () => clearInterval(interval);  // Clear the interval when component unmounts
  }, [isWsOpen]);  // Only re-run the effect if WebSocket connection status changes

  return (
    <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
      <Text>UseRef version</Text>
      <Text>Gyroscope Data: X={gyroscopeDataRef.current.x.toFixed(2)}, Y={gyroscopeDataRef.current.y.toFixed(2)}, Z={gyroscopeDataRef.current.z.toFixed(2)}</Text>
      <Text>Accelerometer Data: X={accelerometerDataRef.current.x.toFixed(2)}, Y={accelerometerDataRef.current.y.toFixed(2)}, Z={accelerometerDataRef.current.z.toFixed(2)}</Text>
    </View>
  );
}
