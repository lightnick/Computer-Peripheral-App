package com.example.androidmouse

import android.annotation.SuppressLint
import android.os.Bundle
import android.view.MotionEvent
import android.view.View
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import java.io.OutputStream
import java.net.Socket

class MainActivity : AppCompatActivity() {

    private var socket: Socket? = null
    private var outputStream: OutputStream? = null
    private lateinit var connectionStatusText: TextView
    private lateinit var ipAddressEditText: EditText
    private lateinit var connectButton: Button
    private lateinit var touchpadView: View
    private lateinit var leftClickButton: Button
    private lateinit var rightClickButton: Button
    private lateinit var scrollWheelView: View

    private var lastX: Float = 0f
    private var lastY: Float = 0f
    private var lastScrollY: Float = 0f

    @SuppressLint("ClickableViewAccessibility")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        // Initialize all UI components
        connectionStatusText = findViewById(R.id.connection_status_text)
        ipAddressEditText = findViewById(R.id.ip_address_edit_text)
        connectButton = findViewById(R.id.connect_button)
        touchpadView = findViewById(R.id.touchpad_view)
        leftClickButton = findViewById(R.id.left_click_button)
        rightClickButton = findViewById(R.id.right_click_button)
        scrollWheelView = findViewById(R.id.scroll_wheel_view)

        // --- Set up Listeners ---

        connectButton.setOnClickListener {
            val ipAddress = ipAddressEditText.text.toString()
            if (ipAddress.isNotEmpty()) {
                connectToServer(ipAddress)
            } else {
                connectionStatusText.text = "Please enter an IP Address"
            }
        }

        leftClickButton.setOnClickListener {
            sendCommand("left_click")
        }

        rightClickButton.setOnClickListener {
            sendCommand("right_click")
        }

        touchpadView.setOnTouchListener {
            _, event ->
            handleTouchpadEvent(event)
        }

        scrollWheelView.setOnTouchListener {
            _, event ->
            handleScrollEvent(event)
        }
    }

    private fun handleTouchpadEvent(event: MotionEvent): Boolean {
        if (!isConnected()) return false

        when (event.action) {
            MotionEvent.ACTION_DOWN -> {
                lastX = event.x
                lastY = event.y
                return true
            }
            MotionEvent.ACTION_MOVE -> {
                val dx = event.x - lastX
                val dy = event.y - lastY
                lastX = event.x
                lastY = event.y

                sendCommand("move ${dx.toInt()},${dy.toInt()}")
                return true
            }
        }
        return false
    }

    private fun handleScrollEvent(event: MotionEvent): Boolean {
        if (!isConnected()) return false

        when (event.action) {
            MotionEvent.ACTION_DOWN -> {
                lastScrollY = event.y
                return true
            }
            MotionEvent.ACTION_MOVE -> {
                val dy = event.y - lastScrollY
                // We send the scroll command for every small movement
                if (kotlin.math.abs(dy) > 1) { // Add a small threshold
                    sendCommand("scroll ${dy.toInt()}")
                    lastScrollY = event.y
                }
                return true
            }
        }
        return false
    }

    private fun sendCommand(command: String) {
        if (isConnected()) {
            Thread {
                try {
                    outputStream?.write((command + "\n").toByteArray())
                } catch (e: Exception) {
                    e.printStackTrace()
                }
            }.start()
        }
    }

    private fun isConnected(): Boolean {
        return socket?.isConnected == true && outputStream != null
    }

    private fun connectToServer(ipAddress: String) {
        Thread {
            try {
                socket?.close()
                runOnUiThread {
                    connectionStatusText.text = "Connecting..."
                }

                socket = Socket(ipAddress, 5000)
                outputStream = socket?.getOutputStream()

                runOnUiThread {
                    connectionStatusText.text = "Connected"
                }
            } catch (e: Exception) {
                e.printStackTrace()
                runOnUiThread {
                    connectionStatusText.text = "Connection Failed: ${e.message}"
                }
            }
        }.start()
    }

    override fun onDestroy() {
        super.onDestroy()
        try {
            socket?.close()
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }
}
