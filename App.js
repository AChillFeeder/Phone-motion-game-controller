import React, { useEffect, useState, useRef } from 'react';
import { View, TouchableOpacity, Button, NativeEventEmitter, NativeModules } from 'react-native';
import { Gyroscope, Accelerometer } from 'expo-sensors';

export default function App() {
  const [isWsOpen, setIsWsOpen] = useState(false);  // WebSocket connection status
  const ws = useRef(null);  // WebSocket reference

  const gyroscopeDataRef = useRef({ x: 0, y: 0, z: 0 });  // Gyroscope data reference
  const accelerometerDataRef = useRef({ x: 0, y: 0, z: 0 });  // Accelerometer data reference
  
  const [currentAction, setCurrentAction] = useState("");

  const reactActionRef = useRef(0);

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

    // Listen for messages from the server
    ws.current.onmessage = (message) => {
      console.log(`Delay: ${Date.now() - reactActionRef.current} ms`);
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

    Gyroscope.setUpdateInterval(1);  // Update every 16ms for 60 FPS

    return () => gyroscopeSubscription && gyroscopeSubscription.remove();
  }, []);

  // Accelerometer data collection
  useEffect(() => {
    const accelerometerSubscription = Accelerometer.addListener((data) => {
      accelerometerDataRef.current = data;  // Update the reference directly
    });

    Accelerometer.setUpdateInterval(1);  // Update every 16ms for 60 FPS

    return () => accelerometerSubscription && accelerometerSubscription.remove();
  }, []);

  useEffect(() => {
    const eventEmitter = new NativeEventEmitter(NativeModules.DeviceEventManagerModule);
    const subscription = eventEmitter.addListener('onVolumeKeyPressed', (key) => {
      if (key === 'volume-up') {
        console.log('Volume Up Pressed');
        setCurrentAction("Volume up")
      } else if (key === 'volume-down') {
        console.log('Volume Down Pressed');
        setCurrentAction("Volume down")
      }
    });

    // Clean up the subscription when the component unmounts
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
          special_action: currentAction,
        };
        setCurrentAction("");  // reset action after sending
        ws.current.send(JSON.stringify(sensorData));
      }
    }, 1);  // Send data every 16ms for 60 FPS

    return () => clearInterval(interval);  // Clear the interval when component unmounts
  }, [isWsOpen, currentAction]);


  function cameraLock() {
    setCurrentAction("Camera lock");
  }
  function deflect() {
    reactActionRef.current = Date.now();
    setCurrentAction("Deflect");
  }


  return (
    <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', height: '80%', gap: 5}}>
      <Button title='Middle button | Camera lock' onPress={cameraLock}/>
      <TouchableOpacity style={{ flex: 1, backgroundColor: 'blue', height: '80%', width: '100%' }} onPress={deflect}>
      </TouchableOpacity>
    </View>
  );
}
