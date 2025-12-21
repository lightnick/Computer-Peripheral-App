package com.example.androidmouse

import android.os.Bundle
import android.view.MotionEvent
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import java.io.OutputStream
import java.net.Socket

class MainActivity : AppCompatActivity() {

    private lateinit var socket: Socket
    private lateinit var outputStream: OutputStream
    private lateinit var connectionStatusText: TextView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        connectionStatusText = findViewById(R.id.connection_status_text)

        Thread {
            try {
                socket = Socket("10.0.2.2", 5000) // Emulator IP address for localhost
                outputStream = socket.getOutputStream()
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

    override fun onTouchEvent(event: MotionEvent?): Boolean {
        if (event != null && event.action == MotionEvent.ACTION_MOVE) {
            if (::outputStream.isInitialized) {
                val coords = "move ${event.x.toInt()},${event.y.toInt()}"
                Thread {
                    try {
                        outputStream.write((coords + "\n").toByteArray())
                    } catch (e: Exception) {
                        e.printStackTrace()
                    }
                }.start()
            }
        }
        return super.onTouchEvent(event)
    }

    override fun onDestroy() {
        super.onDestroy()
        try {
            if (::socket.isInitialized) {
                socket.close()
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }
}
