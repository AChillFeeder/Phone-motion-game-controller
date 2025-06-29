package com.example.motionudp;

import android.app.Activity;
import android.hardware.Sensor;
import android.hardware.SensorEvent;
import android.hardware.SensorEventListener;
import android.hardware.SensorManager;
import android.os.Bundle;
import android.util.Log;
import android.view.MotionEvent;
import android.widget.Button;
import android.widget.EditText;

import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;

public class MainActivity extends Activity implements SensorEventListener {

    private SensorManager sensorManager;
    private Sensor rotationVector;
    private Sensor linearAcceleration;
    private Sensor gyroscope;  // ← NEW

    private InetAddress serverAddress;
    private int serverPort = 9001;

    private volatile boolean lagTestPressed = false;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        try {
            serverAddress = InetAddress.getByName("192.168.1.71");
        } catch (Exception e) {
            e.printStackTrace();
        }

        sensorManager = (SensorManager) getSystemService(SENSOR_SERVICE);
        rotationVector = sensorManager.getDefaultSensor(Sensor.TYPE_ROTATION_VECTOR);
        linearAcceleration = sensorManager.getDefaultSensor(Sensor.TYPE_LINEAR_ACCELERATION);
        gyroscope = sensorManager.getDefaultSensor(Sensor.TYPE_GYROSCOPE);

        if (rotationVector != null)
            sensorManager.registerListener(this, rotationVector, SensorManager.SENSOR_DELAY_GAME);
        if (linearAcceleration != null)
            sensorManager.registerListener(this, linearAcceleration, SensorManager.SENSOR_DELAY_GAME);
        if (gyroscope != null)
            sensorManager.registerListener(this, gyroscope, SensorManager.SENSOR_DELAY_GAME);

        // UI
        Button lagTestButton = findViewById(R.id.lagTestButton);
        EditText ipInput = findViewById(R.id.ipLastSegmentInput);
        Button setIpButton = findViewById(R.id.setIpButton);

        setIpButton.setOnClickListener(v -> {
            String lastSegment = ipInput.getText().toString().trim();
            try {
                if (!lastSegment.isEmpty()) {
                    int segment = Integer.parseInt(lastSegment);
                    if (segment >= 0 && segment <= 255) {
                        String fullIP = "192.168.1." + segment;
                        serverAddress = InetAddress.getByName(fullIP);
                        Log.i("MotionUDP", "IP set to: " + fullIP);
                    }
                }
            } catch (Exception e) {
                Log.e("MotionUDP", "Invalid IP input", e);
            }
        });

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
    }

    @Override
    public void onSensorChanged(SensorEvent event) {
        if (serverAddress == null) return;

        long timestamp = System.currentTimeMillis();
        boolean lag = lagTestPressed;

        switch (event.sensor.getType()) {
            case Sensor.TYPE_ROTATION_VECTOR:
                float[] quat = new float[4];
                SensorManager.getQuaternionFromVector(quat, event.values);
                sendUDP(String.format("rotq,%.5f,%.5f,%.5f,%.5f,%d,%b",
                        quat[1], quat[2], quat[3], quat[0], timestamp, lag));
                break;

            case Sensor.TYPE_LINEAR_ACCELERATION:
                sendUDP(String.format("accel,%.5f,%.5f,%.5f,%d,%b",
                        event.values[0], event.values[1], event.values[2], timestamp, lag));
                break;

            case Sensor.TYPE_GYROSCOPE:  // ← NEW
                sendUDP(String.format("gyro,%.5f,%.5f,%.5f,%d,%b",
                        event.values[0], event.values[1], event.values[2], timestamp, lag));
                break;
        }
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
