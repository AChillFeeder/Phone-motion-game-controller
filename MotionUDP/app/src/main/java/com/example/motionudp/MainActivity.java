package com.example.motionudp;

import android.app.Activity;
import android.hardware.Sensor;
import android.hardware.SensorEvent;
import android.hardware.SensorEventListener;
import android.hardware.SensorManager;
import android.os.Bundle;
import android.util.Log;

import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;

import android.view.MotionEvent;
import android.widget.Button;

public class MainActivity extends Activity implements SensorEventListener {

    private SensorManager sensorManager;
    private Sensor accelerometer, gyroscope;

    private InetAddress serverAddress;
    private int serverPort = 9001;  // Your PC's listening port

    private volatile boolean lagTestPressed = false; // ! -- DEBUG: To calculate delay manually

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // No UI needed
        setContentView(R.layout.activity_main);

        try {
            serverAddress = InetAddress.getByName("192.168.1.71"); //! ← your PC IP - Don't forget to change it!!
        } catch (Exception e) {
            e.printStackTrace();
        }

        sensorManager = (SensorManager) getSystemService(SENSOR_SERVICE);
        accelerometer = sensorManager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER);
        gyroscope = sensorManager.getDefaultSensor(Sensor.TYPE_GYROSCOPE);

        sensorManager.registerListener(this, accelerometer, SensorManager.SENSOR_DELAY_GAME);
        sensorManager.registerListener(this, gyroscope, SensorManager.SENSOR_DELAY_GAME);

        Button lagTestButton = findViewById(R.id.lagTestButton);

        // * DELAY HANDLING
        lagTestButton.setOnTouchListener((v, event) -> {
            switch (event.getAction()) {
                case MotionEvent.ACTION_DOWN:
                    lagTestPressed = true;
                    break;
                case MotionEvent.ACTION_UP:
                case MotionEvent.ACTION_CANCEL:
                    lagTestPressed = false;
                    break;
            }
            return true;
        });
        // * END DELAY HANDLING


    }

    @Override
    public void onSensorChanged(SensorEvent event) {
        if (serverAddress == null) return;

        String type = event.sensor.getType() == Sensor.TYPE_ACCELEROMETER ? "accel" : "gyro";
        float x = event.values[0];
        float y = event.values[1];
        float z = event.values[2];
        long timestamp = System.currentTimeMillis();

        String message = String.format("%s,%.3f,%.3f,%.3f,%d,%b", type, x, y, z, timestamp, lagTestPressed);

        sendUDP(message);
    }

    private void sendUDP(String message) {
        new Thread(() -> {
            try {
                byte[] data = message.getBytes();
                DatagramSocket socket = new DatagramSocket();
                DatagramPacket packet = new DatagramPacket(data, data.length, serverAddress, serverPort);
                socket.send(packet);
                socket.close();
            } catch (Exception e) {
                Log.e("MotionUDP", "Send failed", e);
            }
        }).start();
    }

    @Override
    public void onAccuracyChanged(Sensor sensor, int accuracy) {}
}
