package com.example.androidmouse

import android.annotation.SuppressLint
import android.content.Context
import android.graphics.BitmapFactory
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager
import android.text.Editable
import android.text.TextWatcher
import android.util.Base64
import android.view.GestureDetector
import android.view.KeyEvent
import android.view.MotionEvent
import android.view.View
import android.view.animation.LinearInterpolator
import android.view.inputmethod.InputMethodManager
import android.widget.Button
import android.widget.EditText
import android.widget.ImageView
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.GestureDetectorCompat
import java.io.BufferedReader
import java.io.InputStreamReader
import java.io.OutputStream
import java.net.Socket

class MainActivity : AppCompatActivity() {

    private var socket: Socket? = null
    private var outputStream: OutputStream? = null
    private lateinit var connectionStatusText: TextView
    private lateinit var ipAddressEditText: EditText
    private lateinit var connectButton: Button
    private lateinit var toggleConnectionButton: Button
    private lateinit var connectionSection: View
    private lateinit var keyboardInput: EditText
    private lateinit var touchpadView: View
    private lateinit var cursorView: ImageView
    private lateinit var leftClickButton: Button
    private lateinit var rightClickButton: Button
    private lateinit var scrollWheelView: View

    private var lastX: Float = 0f
    private var lastY: Float = 0f
    private var lastScrollY: Float = 0f

    // Gesture detection
    private lateinit var gestureDetector: GestureDetectorCompat

    // Drag state - controlled by left button press
    private var isLeftButtonPressed = false

    // Keyboard state
    private var isUpdatingKeyboardText = false

    // Haptic feedback
    private lateinit var vibrator: Vibrator

    @SuppressLint("ClickableViewAccessibility")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        // Initialize all UI components
        connectionStatusText = findViewById(R.id.connection_status_text)
        ipAddressEditText = findViewById(R.id.ip_address_edit_text)
        connectButton = findViewById(R.id.connect_button)
        toggleConnectionButton = findViewById(R.id.toggle_connection_button)
        connectionSection = findViewById(R.id.connection_section)
        keyboardInput = findViewById(R.id.keyboard_input)
        touchpadView = findViewById(R.id.touchpad_view)
        cursorView = findViewById(R.id.cursor_view)
        leftClickButton = findViewById(R.id.left_click_button)
        rightClickButton = findViewById(R.id.right_click_button)
        scrollWheelView = findViewById(R.id.scroll_wheel_view)

        // Initialize gesture detector
        gestureDetector = GestureDetectorCompat(this, TouchpadGestureListener())

        // Initialize vibrator for haptic feedback
        try {
            vibrator = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                val vibratorManager = getSystemService(Context.VIBRATOR_MANAGER_SERVICE) as VibratorManager
                vibratorManager.defaultVibrator
            } else {
                @Suppress("DEPRECATION")
                getSystemService(Context.VIBRATOR_SERVICE) as Vibrator
            }
        } catch (e: Exception) {
            e.printStackTrace()
            // Vibrator will be initialized but may not work - safe to continue
        }

        // Set up keyboard input listener
        setupKeyboardInput()

        // --- Set up Listeners ---

        toggleConnectionButton.setOnClickListener {
            toggleConnectionSection()
        }

        connectButton.setOnClickListener {
            val ipAddress = ipAddressEditText.text.toString()
            if (ipAddress.isNotEmpty()) {
                connectToServer(ipAddress)
            } else {
                connectionStatusText.text = "Please enter an IP Address"
            }
        }

        // Left button now supports press-and-hold for dragging
        leftClickButton.setOnTouchListener { view, event ->
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    view.isPressed = true  // Set pressed state for visual feedback
                    isLeftButtonPressed = true
                    sendCommand("drag_start")
                    vibrateClick()  // Haptic feedback
                    true
                }
                MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                    view.isPressed = false  // Remove pressed state
                    if (isLeftButtonPressed) {
                        isLeftButtonPressed = false
                        sendCommand("drag_end")
                    }
                    true
                }
                else -> false
            }
        }

        rightClickButton.setOnTouchListener { view, event ->
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    view.isPressed = true  // Set pressed state for visual feedback
                    true
                }
                MotionEvent.ACTION_UP -> {
                    view.isPressed = false  // Remove pressed state
                    if (event.x >= 0 && event.x <= view.width &&
                        event.y >= 0 && event.y <= view.height) {
                        // Only trigger click if touch ended within button bounds
                        sendCommand("right_click")
                        vibrateClick()  // Haptic feedback
                    }
                    true
                }
                MotionEvent.ACTION_CANCEL -> {
                    view.isPressed = false  // Remove pressed state
                    true
                }
                else -> false
            }
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

        // Pass to gesture detector for double-tap and long-press detection
        gestureDetector.onTouchEvent(event)

        val pointerCount = event.pointerCount

        when (event.actionMasked) {
            MotionEvent.ACTION_DOWN -> {
                lastX = event.x
                lastY = event.y
                return true
            }

            MotionEvent.ACTION_POINTER_DOWN -> {
                // Multi-finger tap detection
                if (pointerCount == 3) {
                    // Three-finger tap = middle-click
                    sendCommand("middle_click")
                }
                return true
            }

            MotionEvent.ACTION_MOVE -> {
                // Only handle single-finger movement for mouse/drag
                if (pointerCount == 1) {
                    val dx = event.x - lastX
                    val dy = event.y - lastY
                    lastX = event.x
                    lastY = event.y

                    // Send drag_move if left button is pressed, otherwise normal move
                    if (isLeftButtonPressed) {
                        sendCommand("drag_move ${dx.toInt()},${dy.toInt()}")
                    } else {
                        sendCommand("move ${dx.toInt()},${dy.toInt()}")
                    }
                }
                return true
            }

            MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                // No action needed - drag is controlled by left button
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

                    // Staggered vibration for scroll feedback
                    vibrateScroll()
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
                    // Auto-collapse and hide connection UI after successful connection
                    connectionSection.visibility = View.GONE
                    toggleConnectionButton.text = "⚙"  // Settings gear icon
                    connectionStatusText.visibility = View.INVISIBLE  // Keep space but invisible
                }

                // Start listening for messages from server
                startServerMessageListener()

                // Enable cursor view
                sendCommand("cursor_view on")

            } catch (e: Exception) {
                e.printStackTrace()
                runOnUiThread {
                    connectionStatusText.text = "Connection Failed: ${e.message}"
                }
            }
        }.start()
    }

    private fun startServerMessageListener() {
        Thread {
            try {
                val reader = BufferedReader(InputStreamReader(socket?.getInputStream()))
                while (socket?.isConnected == true) {
                    val message = reader.readLine() ?: break
                    handleServerMessage(message)
                }
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }.start()
    }

    private fun handleServerMessage(message: String) {
        when {
            message.trim() == "TEXTBOX_FOCUSED" -> {
                println("[DEBUG] TEXTBOX_FOCUSED received, showing keyboard")
                runOnUiThread {
                    showKeyboard()
                }
            }
            message.startsWith("CURSOR_VIEW ") -> {
                // Decode and display cursor image
                val base64Image = message.substring(12)  // Remove "CURSOR_VIEW " prefix
                try {
                    val imageBytes = Base64.decode(base64Image, Base64.DEFAULT)
                    val bitmap = BitmapFactory.decodeByteArray(imageBytes, 0, imageBytes.size)
                    runOnUiThread {
                        cursorView.setImageBitmap(bitmap)
                        cursorView.visibility = View.VISIBLE
                    }
                } catch (e: Exception) {
                    println("[ERROR] Failed to decode cursor image: ${e.message}")
                }
            }
            else -> {
                println("[DEBUG] Unknown message: $message")
            }
        }
    }

    private fun setupKeyboardInput() {
        var lastText = ""

        // Handle special keys FIRST (before TextWatcher)
        keyboardInput.setOnKeyListener { _, keyCode, event ->
            if (event.action == KeyEvent.ACTION_DOWN) {
                when (keyCode) {
                    KeyEvent.KEYCODE_DEL -> {
                        // Backspace key pressed
                        sendCommand("key backspace")
                        println("[DEBUG] Backspace key pressed")
                        false  // Let Android handle the deletion in the EditText too
                    }
                    KeyEvent.KEYCODE_ENTER -> {
                        sendCommand("key enter")
                        println("[DEBUG] Enter key pressed")
                        true
                    }
                    else -> false
                }
            } else {
                false
            }
        }

        // Handle regular typing
        keyboardInput.addTextChangedListener(object : TextWatcher {
            override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int, after: Int) {
                if (!isUpdatingKeyboardText) {
                    lastText = s?.toString() ?: ""
                }
            }

            override fun onTextChanged(s: CharSequence?, start: Int, before: Int, count: Int) {
                // Skip if we're programmatically updating
                if (isUpdatingKeyboardText) return

                val currentText = s?.toString() ?: ""

                // Only handle text addition (backspace is handled by setOnKeyListener)
                if (currentText.length > lastText.length) {
                    val newChars = currentText.substring(lastText.length)
                    newChars.forEach { char ->
                        sendCommand("type $char")
                        println("[DEBUG] Typed: $char")
                    }
                }
            }

            override fun afterTextChanged(s: Editable?) {
                // Not needed
            }
        })
    }

    private fun showKeyboard() {
        println("[DEBUG] showKeyboard() called")
        runOnUiThread {
            keyboardInput.visibility = View.VISIBLE
            // Clear previous text without triggering TextWatcher
            isUpdatingKeyboardText = true
            keyboardInput.setText("")
            isUpdatingKeyboardText = false

            keyboardInput.requestFocus()
            val imm = getSystemService(Context.INPUT_METHOD_SERVICE) as InputMethodManager
            imm.showSoftInput(keyboardInput, InputMethodManager.SHOW_FORCED)
            println("[DEBUG] Keyboard show requested")
        }
    }

    private fun hideKeyboard() {
        val imm = getSystemService(Context.INPUT_METHOD_SERVICE) as InputMethodManager
        imm.hideSoftInputFromWindow(currentFocus?.windowToken, 0)
        keyboardInput.visibility = View.GONE
    }

    private fun toggleConnectionSection() {
        if (connectionSection.visibility == View.VISIBLE) {
            // Hide the connection section
            connectionSection.visibility = View.GONE
            toggleConnectionButton.text = "▶"  // Right arrow when collapsed
        } else {
            // Show the connection section and connection UI
            connectionSection.visibility = View.VISIBLE
            toggleConnectionButton.visibility = View.VISIBLE
            connectionStatusText.visibility = View.VISIBLE
            toggleConnectionButton.text = "▼"  // Down arrow when expanded
        }
    }

    // Gesture listener for double-tap and single-tap
    private inner class TouchpadGestureListener : GestureDetector.SimpleOnGestureListener() {

        override fun onDoubleTap(e: MotionEvent): Boolean {
            sendCommand("double_click")
            return true
        }

        override fun onSingleTapConfirmed(e: MotionEvent): Boolean {
            // Single tap = Quick left click (without keyboard detection)
            sendCommand("click")
            return true
        }
    }

    private fun vibrateClick() {
        // Short vibration for click feedback (20ms)
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                vibrator.vibrate(VibrationEffect.createOneShot(20, VibrationEffect.DEFAULT_AMPLITUDE))
            } else {
                @Suppress("DEPRECATION")
                vibrator.vibrate(20)
            }
        } catch (e: Exception) {
            // Ignore vibration errors
        }
    }

    private fun vibrateScroll() {
        // Very short staggered vibration for scroll feedback (10ms)
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                vibrator.vibrate(VibrationEffect.createOneShot(10, VibrationEffect.DEFAULT_AMPLITUDE))
            } else {
                @Suppress("DEPRECATION")
                vibrator.vibrate(10)
            }
        } catch (e: Exception) {
            // Ignore vibration errors
        }
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
