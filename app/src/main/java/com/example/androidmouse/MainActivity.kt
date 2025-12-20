package com.example.androidmouse

import android.os.Bundle
import android.view.MotionEvent
import androidx.appcompat.app.AppCompatActivity
import java.io.OutputStream
import java.net.Socket

class MainActivity : AppCompatActivity() {

    private lateinit var socket: Socket
    private lateinit var outputStream: OutputStream

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        Thread {
            try {
                socket = Socket("192.168.1.100", 5000) // Replace with server IP address
                outputStream = socket.getOutputStream()
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }.start()
    }

    override fun onTouchEvent(event: MotionEvent?): Boolean {
        if (event != null && event.action == MotionEvent.ACTION_MOVE) {
            val coords = "${event.x.toInt()},${event.y.toInt()}"
            Thread {
                try {
                    outputStream.write((coords + "\n").toByteArray())
                } catch (e: Exception) {
                    e.printStackTrace()
                }
            }.start()
        }
        return super.onTouchEvent(event)
    }

    override fun onDestroy() {
        super.onDestroy()
        try {
            socket.close()
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }
}