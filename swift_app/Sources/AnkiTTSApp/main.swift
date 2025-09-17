import Foundation
import AppKit

// ANSI color codes for beautiful terminal output
struct Colors {
    static let red = "\u{001B}[0;31m"
    static let green = "\u{001B}[0;32m"
    static let yellow = "\u{001B}[1;33m"
    static let blue = "\u{001B}[0;34m"
    static let purple = "\u{001B}[0;35m"
    static let cyan = "\u{001B}[0;36m"
    static let white = "\u{001B}[1;37m"
    static let bold = "\u{001B}[1m"
    static let reset = "\u{001B}[0m"
}

// Helper functions for colored output
func printColored(_ message: String, color: String = Colors.white, bold: Bool = false) {
    let style = bold ? Colors.bold : ""
    print("\(style)\(color)\(message)\(Colors.reset)")
}

func printStatus(_ message: String) {
    printColored("▶ \(message)", color: Colors.blue, bold: true)
}

func printSuccess(_ message: String) {
    printColored("✅ \(message)", color: Colors.green, bold: true)
}

func printWarning(_ message: String) {
    printColored("⚠️  \(message)", color: Colors.yellow, bold: true)
}

func printError(_ message: String) {
    printColored("❌ \(message)", color: Colors.red, bold: true)
}

func printInfo(_ message: String) {
    printColored("ℹ️  \(message)", color: Colors.cyan, bold: true)
}

func printHeader(_ title: String) {
    printColored("╔══════════════════════════════════════════════════════════════╗", color: Colors.cyan, bold: true)
    printColored("║                    \(title)                    ║", color: Colors.cyan, bold: true)
    printColored("╚══════════════════════════════════════════════════════════════╝", color: Colors.cyan, bold: true)
}

// Add a single-instance manager to prevent multiple instances of the app
class SingleInstanceManager {
    static let shared = SingleInstanceManager()
    private let lockFilePath: URL
    
    private init() {
        let tempDir = FileManager.default.temporaryDirectory
        lockFilePath = tempDir.appendingPathComponent("ankitts.lock")
    }
    
    func checkAndLock() -> Bool {
        let fileManager = FileManager.default
        
        // Kill any existing Python processes first
        killExistingPythonProcesses()
        
        // Check if lock file exists
        if fileManager.fileExists(atPath: lockFilePath.path) {
            do {
                // Try to read the PID
                let pidString = try String(contentsOf: lockFilePath, encoding: .utf8)
                if let pid = Int32(pidString.trimmingCharacters(in: .whitespacesAndNewlines)) {
                    // Check if process is still running
                    if kill(pid, 0) == 0 {
                        // Process exists, can't launch another instance
                        printWarning("Another instance is already running with PID: \(pid)")
                        return false
                    } else {
                        // Process doesn't exist, file is stale
                        try? fileManager.removeItem(at: lockFilePath)
                    }
                }
            } catch {
                // Error reading file, assume it's stale
                try? fileManager.removeItem(at: lockFilePath)
            }
        }
        
        // Create lock file with our PID
        do {
            let pid = ProcessInfo.processInfo.processIdentifier
            try "\(pid)".write(to: lockFilePath, atomically: true, encoding: .utf8)
            
            // Setup cleanup on exit
            atexit {
                try? FileManager.default.removeItem(at: SingleInstanceManager.shared.lockFilePath)
            }
            
            return true
        } catch {
            printError("Failed to create lock file: \(error)")
            return false
        }
    }
    
    private func killExistingPythonProcesses() {
        let task = Process()
        task.executableURL = URL(fileURLWithPath: "/usr/bin/pkill")
        task.arguments = ["-f", "python -u.*anki_tts\\.py"]
        
        do {
            try task.run()
            task.waitUntilExit()
            printSuccess("Cleaned up any existing Python processes")
        } catch {
            printError("Error cleaning up Python processes: \(error)")
        }
    }
}

class AnkiTTSController: NSObject, NSApplicationDelegate {
    var statusItem: NSStatusItem!
    var pythonProcess: Process?
    var ttsSpeed: Float = 1.5 // Default speed
    
    func applicationDidFinishLaunching(_ notification: Notification) {
        printHeader("🚀 Anki TTS Application 🚀")
        printStatus("Initializing menu bar application...")
        
        // Create status bar item
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.squareLength)
        if let button = statusItem.button {
            button.image = NSImage(systemSymbolName: "speaker.wave.2", accessibilityDescription: "Anki TTS")
        }
        
        printSuccess("Menu bar item created")
        
        // Create the menu
        setupMenu()
        printSuccess("Menu configured")
        
        // Start the Python script immediately
        startPythonScript()
    }
    
    func setupMenu() {
        let menu = NSMenu()
        
        // Status item
        let statusMenuItem = NSMenuItem(title: "Anki TTS: Connected", action: nil, keyEquivalent: "")
        statusMenuItem.isEnabled = false
        menu.addItem(statusMenuItem)
        
        menu.addItem(NSMenuItem.separator())
        
        // Speed submenu
        let speedMenuItem = NSMenuItem(title: "Speed", action: nil, keyEquivalent: "")
        let speedSubmenu = NSMenu()
        speedMenuItem.submenu = speedSubmenu
        
        // Add speed options from 1.0 to 1.8 in 0.1 increments
        for speed in stride(from: 1.0, through: 1.8, by: 0.1) {
            let speedValue = Float(round(speed * 10) / 10) // Round to 1 decimal place
            let speedItem = NSMenuItem(
                title: String(format: "%.1fx", speedValue),
                action: #selector(setSpeed(_:)),
                keyEquivalent: ""
            )
            speedItem.representedObject = speedValue
            speedItem.state = speedValue == ttsSpeed ? .on : .off
            speedSubmenu.addItem(speedItem)
        }
        
        menu.addItem(speedMenuItem)
        
        menu.addItem(NSMenuItem.separator())
        
        // Quit item
        menu.addItem(NSMenuItem(title: "Quit", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q"))
        
        statusItem.menu = menu
    }
    
    @objc func setSpeed(_ sender: NSMenuItem) {
        guard let speedValue = sender.representedObject as? Float else { return }
        
        // Update the speed
        ttsSpeed = speedValue
        
        // Update the menu items
        if let speedMenu = sender.menu {
            for item in speedMenu.items {
                if let itemSpeed = item.representedObject as? Float {
                    item.state = itemSpeed == ttsSpeed ? .on : .off
                }
            }
        }
        
        // Send the speed to the Python script
        updatePythonSpeed()
    }
    
    func updatePythonSpeed() {
        // Write the speed to a fixed location that Python will check
        let tempDir = FileManager.default.temporaryDirectory
        let speedFilePath = tempDir.appendingPathComponent("anki_tts_speed_control.txt")
        
        do {
            // Write just the speed value
            try String(ttsSpeed).write(to: speedFilePath, atomically: true, encoding: .utf8)
            printInfo("Speed updated to: \(ttsSpeed)x")
        } catch {
            printError("Error writing speed to file: \(error)")
        }
    }
    
    func startPythonScript() {
        printStatus("Starting Python TTS engine...")
        
        // Get the path to the Python script
        let scriptPath = findPythonScript()
        guard let scriptPath = scriptPath else {
            printError("Could not find anki_tts.py")
            return
        }
        
        printSuccess("Found script at: \(scriptPath)")
        
        // Write the initial speed to the file (set to 1.5x default)
        ttsSpeed = 1.5
        updatePythonSpeed()
        
        // Pass the initial speed as a command-line argument too (belt and suspenders)
        let initialSpeedArg = String(ttsSpeed)
        
        // Create and configure the process
        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/usr/bin/env")
        process.arguments = ["uv", "run", "--directory", "..", "python", "-u", scriptPath, initialSpeedArg]
        process.currentDirectoryURL = URL(fileURLWithPath: (scriptPath as NSString).deletingLastPathComponent)
        
        // Set up pipes for output and error
        let outputPipe = Pipe()
        let errorPipe = Pipe()
        process.standardOutput = outputPipe
        process.standardError = errorPipe
        
        // Set up output handling
        let outputHandle = outputPipe.fileHandleForReading
        outputHandle.waitForDataInBackgroundAndNotify()
        
        NotificationCenter.default.addObserver(
            forName: NSNotification.Name.NSFileHandleDataAvailable,
            object: outputHandle,
            queue: nil
        ) { [weak self] notification in
            let data = outputHandle.availableData
            if !data.isEmpty {
                if let output = String(data: data, encoding: .utf8)?.trimmingCharacters(in: .whitespacesAndNewlines),
                   !output.isEmpty {
                    print("Python output: \(output)")
                    
                    // Update status item title if needed
                    if output.contains("Reading:") {
                        DispatchQueue.main.async {
                            if let menu = self?.statusItem.menu {
                                if let statusItem = menu.items.first {
                                    statusItem.title = "Anki TTS: Reading..."
                                }
                            }
                        }
                    } else if output.contains("Waiting") {
                        DispatchQueue.main.async {
                            if let menu = self?.statusItem.menu {
                                if let statusItem = menu.items.first {
                                    statusItem.title = "Anki TTS: Waiting"
                                }
                            }
                        }
                    }
                }
                outputHandle.waitForDataInBackgroundAndNotify()
            }
        }
        
        // Set up error handling
        let errorHandle = errorPipe.fileHandleForReading
        errorHandle.waitForDataInBackgroundAndNotify()
        
        NotificationCenter.default.addObserver(
            forName: NSNotification.Name.NSFileHandleDataAvailable,
            object: errorHandle,
            queue: nil
        ) { notification in
            let data = errorHandle.availableData
            if !data.isEmpty {
                if let output = String(data: data, encoding: .utf8)?.trimmingCharacters(in: .whitespacesAndNewlines),
                   !output.isEmpty {
                    print("Python error: \(output)")
                }
                errorHandle.waitForDataInBackgroundAndNotify()
            }
        }
        
        // Start the process
        do {
            try process.run()
            pythonProcess = process
            printSuccess("Python TTS process started successfully")
        } catch {
            printError("Failed to start Python process: \(error)")
        }
    }
    
    func findPythonScript() -> String? {
        printStatus("Searching for anki_tts.py...")
        printInfo("Current directory: \(FileManager.default.currentDirectoryPath)")
        
        // Try multiple possible locations
        let possibleLocations = [
            // First try Resources directory
            FileManager.default.currentDirectoryPath + "/Resources/anki_tts.py",
            // Then try relative paths
            FileManager.default.currentDirectoryPath + "/anki_tts.py",
            FileManager.default.currentDirectoryPath + "/../Resources/anki_tts.py",
            // Try absolute path as fallback
            "/Users/lucascamillo/anki-tts/swift_app/Resources/anki_tts.py"
        ]
        
        printStatus("Checking possible locations:")
        for path in possibleLocations {
            printInfo("Checking: \(path)")
            if FileManager.default.fileExists(atPath: path) {
                printSuccess("Found Python script at: \(path)")
                return path
            }
        }
        
        printError("Could not find anki_tts.py in any location")
        return nil
    }
    
    func applicationWillTerminate(_ notification: Notification) {
        pythonProcess?.terminate()
    }
}

// Create and run the application
autoreleasepool {
    // Check if another instance is already running
    if !SingleInstanceManager.shared.checkAndLock() {
        printError("Another instance of Anki TTS is already running. Exiting.")
        exit(0)
    }
    
    let app = NSApplication.shared
    app.setActivationPolicy(.accessory) // Use .accessory for menu bar app
    
    let controller = AnkiTTSController()
    app.delegate = controller
    
    // Create a minimal menu to allow proper app behavior
    let menubar = NSMenu()
    app.mainMenu = menubar
    
    // App Menu
    let appMenuItem = NSMenuItem()
    menubar.addItem(appMenuItem)
    let appMenu = NSMenu()
    appMenuItem.submenu = appMenu
    
    appMenu.addItem(NSMenuItem(title: "Quit Anki TTS", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q"))
    
    app.run()
}
