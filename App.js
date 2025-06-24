import React, { useEffect, useState, useRef, useCallback } from 'react';
import { View, TouchableOpacity, Button, NativeEventEmitter, NativeModules } from 'react-native';
import { Gyroscope, Accelerometer } from 'expo-sensors';

export default function App() {
  const [isWsOpen, setIsWsOpen] = useState(false);  // WebSocket connection status
  const ws = useRef(null);  // WebSocket reference

  const gyroscopeDataRef = useRef({ x: 0, y: 0, z: 0 });  // Gyroscope data reference
  const accelerometerDataRef = useRef({ x: 0, y: 0, z: 0 });  // Accelerometer data reference

  const reactActionRef = useRef(0);  // To store the action timestamp
  const currentActionRef = useRef("");  // Store action in ref to avoid state re-renders
  const reportedDelay = useRef(0);

  const delay = 16;

  // Initialize WebSocket connection
  useEffect(() => {
    ws.current = new WebSocket('ws://192.168.1.71:6790');  // ! Replace with your server's IP and port

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

    // Listen for messages from the server
    ws.current.onmessage = (message) => {
      reportedDelay.current = Date.now() - reactActionRef.current
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

    Gyroscope.setUpdateInterval(delay);  // Update every 16ms for 60 FPS

    return () => gyroscopeSubscription && gyroscopeSubscription.remove();
  }, []);

  // Accelerometer data collection
  useEffect(() => {
    const accelerometerSubscription = Accelerometer.addListener((data) => {
      accelerometerDataRef.current = data;  // Update the reference directly
    });

    Accelerometer.setUpdateInterval(delay);  // Update every 16ms for 60 FPS

    return () => accelerometerSubscription && accelerometerSubscription.remove();
  }, []);

  // Listen for volume button presses
  useEffect(() => {
    const eventEmitter = new NativeEventEmitter(NativeModules.DeviceEventManagerModule);
    const subscription = eventEmitter.addListener('onVolumeKeyPressed', (key) => {
      if (key === 'volume-up') {
        console.log('Volume Up Pressed');
        currentActionRef.current = "Volume up";  // Store action in ref to avoid re-render
      } else if (key === 'volume-down') {
        console.log('Volume Down Pressed');
        currentActionRef.current = "Volume down";
      }
    });

    return () => {
      subscription.remove();
    };
  }, []);

  // Send sensor data and volume button actions to WebSocket
  useEffect(() => {
    const interval = setInterval(() => {
      if (isWsOpen && ws.current && ws.current.readyState === WebSocket.OPEN) {
        const sensorData = {
          gyroscope: gyroscopeDataRef.current,
          accelerometer: accelerometerDataRef.current,
          special_action: currentActionRef.current,  // Use ref instead of state to avoid re-renders
          delay: reportedDelay.current
        };
        currentActionRef.current = "";  // Reset action after sending
        ws.current.send(JSON.stringify(sensorData));
      }
    }, delay);  // Send data every 16ms (matching 60 FPS)

    return () => clearInterval(interval);  // Clear the interval when component unmounts
  }, [isWsOpen]);

  // Camera lock action handler
  const cameraLock = useCallback(() => {
    currentActionRef.current = "Camera lock";
  }, []);

  // Deflect action handler
  const deflect = useCallback(() => {
    reactActionRef.current = Date.now();
    currentActionRef.current = "Deflect";
  }, []);

  return (
    <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', height: '80%', gap: 5}}>
      <Button title='Middle button | Camera lock' onPress={cameraLock} />
      <TouchableOpacity
        style={{ flex: 1, backgroundColor: 'blue', height: '80%', width: '100%' }}
        onPress={deflect}
      />
    </View>
  );
}
