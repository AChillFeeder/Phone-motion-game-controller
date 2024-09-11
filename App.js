import React, { useEffect, useState, useRef } from 'react';
import { View, Text, Button, NativeEventEmitter, NativeModules } from 'react-native';
import { Gyroscope, Accelerometer, DeviceMotion } from 'expo-sensors';

export default function App() {
  const [isWsOpen, setIsWsOpen] = useState(false);  // WebSocket connection status
  const ws = useRef(null);  // WebSocket reference
  const gyroscopeDataRef = useRef({ x: 0, y: 0, z: 0 });  // Gyroscope data reference
  const accelerometerDataRef = useRef({ x: 0, y: 0, z: 0 });  // Accelerometer data reference
  const [currentAction, setCurrentAction] = useState("");

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
    });

    Gyroscope.setUpdateInterval(1);  // Update every 1ms

    return () => gyroscopeSubscription && gyroscopeSubscription.remove();
  }, []);

  // Accelerometer data collection
  useEffect(() => {
    const accelerometerSubscription = Accelerometer.addListener((data) => {
      accelerometerDataRef.current = data;  // Update the reference directly
    });

    Accelerometer.setUpdateInterval(1);  // Update every 1ms

    return () => accelerometerSubscription && accelerometerSubscription.remove();
  }, []);

  // Detect volume button presses and handle actions
  useEffect(() => {
    const eventEmitter = new NativeEventEmitter(NativeModules.DeviceEventManagerModule);
    
    const volumeListener = eventEmitter.addListener('onVolumeKeyPressed', (key) => {
      if (key === 'volume-up') {
        console.log('Volume Up Pressed');
        setCurrentAction("Volume up");
      } else if (key === 'volume-down') {
        console.log('Volume Down Pressed');
        setCurrentAction("Volume down");
      }
    });

    // Clean up when the component unmounts
    return () => {
      volumeListener.remove();
    };
  }, []);

  // Send sensor data and volume button actions to WebSocket every second
  useEffect(() => {
    const interval = setInterval(() => {
      if (currentAction !== "") {
        console.log("Current action sent to server: ", currentAction);
      }
      if (isWsOpen && ws.current && ws.current.readyState === WebSocket.OPEN) {
        const sensorData = {
          gyroscope: gyroscopeDataRef.current,  // Access the latest data from the refs
          accelerometer: accelerometerDataRef.current,
          special_action: currentAction,
        };
        setCurrentAction(""); // reset action after sending
        ws.current.send(JSON.stringify(sensorData));  // Send the sensor data
      }
    }, 1);  // Send data every second

    return () => clearInterval(interval);  // Clear the interval when component unmounts
  }, [isWsOpen, currentAction]);  // Only re-run the effect if WebSocket connection status changes

  function cameraLock() {
    setCurrentAction("Camera lock");
  }
  function heal() {
    setCurrentAction("Heal");
  }

  return (
    <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
      <Text>UseRef version</Text>
      <Button title='Camera lock' onPress={cameraLock} />
      <Button title='Heal' onPress={heal} />
    </View>
  );
}
