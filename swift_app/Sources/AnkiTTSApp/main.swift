import Foundation
import AppKit

class AnkiTTSController: NSObject, NSApplicationDelegate, NSWindowDelegate {
    var window: NSWindow!
    var scrollView: NSScrollView!
    var textView: NSTextView!
    var pythonProcess: Process?
    var statusView: NSView!
    var statusLabel: NSTextField!
    var clearButton: NSButton!
    var showAnswerButton: NSButton!
    var answerButtonsView: NSView!
    var answerButtons: [NSButton] = []
    var recognizer: NSSpeechRecognizer?
    let voiceCommands = [
        "show", "show answer",
        "again", "repeat",
        "hard", "difficult",
        "good", "okay",
        "easy", "simple"
    ]
    
    func createAnswerButton(title: String, color: NSColor, action: Selector, frame: NSRect) -> NSButton {
        let button = NSButton(frame: frame)
        button.title = title
        button.bezelStyle = .rounded
        button.isBordered = true
        button.wantsLayer = true
        button.layer?.backgroundColor = color.cgColor
        button.layer?.cornerRadius = 6
        button.target = self
        button.action = action
        button.isHidden = true  // Initially hidden
        return button
    }
    
    func applicationDidFinishLaunching(_ notification: Notification) {
        print("Application starting...")
        
        // Create window with a nice size and make it resizable
        let windowRect = NSRect(x: 0, y: 0, width: 800, height: 600)
        window = NSWindow(
            contentRect: windowRect,
            styleMask: [.titled, .closable, .miniaturizable, .resizable, .fullSizeContentView],
            backing: .buffered,
            defer: false
        )
        window.delegate = self
        window.title = "Anki TTS"
        window.titlebarAppearsTransparent = true
        window.titleVisibility = .visible
        window.center()
        window.minSize = NSSize(width: 600, height: 400)
        window.backgroundColor = NSColor(calibratedRed: 0.12, green: 0.12, blue: 0.15, alpha: 1.0)
        
        // Create content view with a gradient background
        let contentView = NSView(frame: window.contentView!.bounds)
        contentView.wantsLayer = true
        contentView.autoresizingMask = [.width, .height]
        
        let gradient = CAGradientLayer()
        gradient.frame = contentView.bounds
        gradient.colors = [
            NSColor(calibratedRed: 0.18, green: 0.20, blue: 0.25, alpha: 1.0).cgColor,
            NSColor(calibratedRed: 0.12, green: 0.14, blue: 0.18, alpha: 1.0).cgColor
        ]
        contentView.layer = gradient
        window.contentView = contentView
        
        // Create status view with blur effect
        let statusHeight: CGFloat = 50
        statusView = NSVisualEffectView(frame: NSRect(
            x: 0,
            y: contentView.frame.height - statusHeight,
            width: contentView.frame.width,
            height: statusHeight
        ))
        (statusView as! NSVisualEffectView).material = .hudWindow
        (statusView as! NSVisualEffectView).state = .active
        (statusView as! NSVisualEffectView).blendingMode = .behindWindow
        statusView.wantsLayer = true
        statusView.autoresizingMask = [.width, .minYMargin]
        contentView.addSubview(statusView)
        
        // Create answer buttons container view with blur effect
        let buttonBarHeight: CGFloat = 60
        answerButtonsView = NSVisualEffectView(frame: NSRect(
            x: 0,
            y: 0,
            width: contentView.frame.width,
            height: buttonBarHeight
        ))
        (answerButtonsView as! NSVisualEffectView).material = .hudWindow
        (answerButtonsView as! NSVisualEffectView).state = .active
        (answerButtonsView as! NSVisualEffectView).blendingMode = .behindWindow
        answerButtonsView.wantsLayer = true
        answerButtonsView.autoresizingMask = [.width, .maxYMargin]
        contentView.addSubview(answerButtonsView)
        
        // Add status label with modern styling
        statusLabel = NSTextField(frame: NSRect(x: 20, y: 15, width: 300, height: 20))
        statusLabel.stringValue = "Connected to Anki"
        statusLabel.isEditable = false
        statusLabel.isBordered = false
        statusLabel.backgroundColor = .clear
        statusLabel.textColor = NSColor(calibratedWhite: 0.9, alpha: 1.0)
        statusLabel.font = NSFont.systemFont(ofSize: 13, weight: .medium)
        statusView.addSubview(statusLabel)
        
        // Add clear button with modern styling
        clearButton = NSButton(frame: NSRect(x: contentView.frame.width - 120, y: 10, width: 100, height: 30))
        clearButton.title = "Clear Log"
        clearButton.bezelStyle = .rounded
        clearButton.isBordered = true
        clearButton.wantsLayer = true
        clearButton.layer?.backgroundColor = NSColor(calibratedWhite: 1.0, alpha: 0.1).cgColor
        clearButton.layer?.cornerRadius = 6
        clearButton.target = self
        clearButton.action = #selector(clearLog)
        clearButton.autoresizingMask = [.minXMargin]
        statusView.addSubview(clearButton)
        
        // Calculate button widths and spacing for all buttons
        let buttonWidth: CGFloat = 120
        let spacing: CGFloat = 16
        let totalWidth = (buttonWidth * 5) + (spacing * 4)
        let startX = (contentView.frame.width - totalWidth) / 2
        
        // Create Show Answer button with modern styling
        showAnswerButton = NSButton(frame: NSRect(x: startX, y: 15, width: buttonWidth, height: 30))
        showAnswerButton.title = "Show"
        showAnswerButton.bezelStyle = .rounded
        showAnswerButton.isBordered = true
        showAnswerButton.wantsLayer = true
        showAnswerButton.layer?.backgroundColor = NSColor(calibratedRed: 0.3, green: 0.6, blue: 1.0, alpha: 0.3).cgColor
        showAnswerButton.layer?.cornerRadius = 8
        showAnswerButton.target = self
        showAnswerButton.action = #selector(showAnswer)
        answerButtonsView.addSubview(showAnswerButton)
        
        // Create answer buttons with modern styling
        let buttonConfigs = [
            ("Again", NSColor(calibratedRed: 0.9, green: 0.3, blue: 0.3, alpha: 0.3), #selector(answerAgain)),
            ("Hard", NSColor(calibratedRed: 0.9, green: 0.5, blue: 0.2, alpha: 0.3), #selector(answerHard)),
            ("Good", NSColor(calibratedRed: 0.3, green: 0.8, blue: 0.4, alpha: 0.3), #selector(answerGood)),
            ("Easy", NSColor(calibratedRed: 0.2, green: 0.9, blue: 0.4, alpha: 0.3), #selector(answerEasy))
        ]
        
        for (index, (title, color, action)) in buttonConfigs.enumerated() {
            let x = startX + CGFloat(index + 1) * (buttonWidth + spacing)
            let button = createAnswerButton(
                title: title,
                color: color,
                action: action,
                frame: NSRect(x: x, y: 15, width: buttonWidth, height: 30)
            )
            answerButtonsView.addSubview(button)
            answerButtons.append(button)
        }
        
        // Adjust scroll view for modern look
        let scrollViewInsets = NSEdgeInsets(top: 20, left: 20, bottom: buttonBarHeight + 20, right: 20)
        scrollView = NSScrollView(frame: NSRect(
            x: scrollViewInsets.left,
            y: scrollViewInsets.bottom,
            width: contentView.frame.width - scrollViewInsets.left - scrollViewInsets.right,
            height: contentView.frame.height - statusHeight - scrollViewInsets.top - scrollViewInsets.bottom
        ))
        scrollView.hasVerticalScroller = true
        scrollView.hasHorizontalScroller = false
        scrollView.autoresizingMask = [.width, .height]
        scrollView.borderType = .noBorder
        scrollView.drawsBackground = false
        contentView.addSubview(scrollView)
        
        // Create text view with modern styling
        let contentSize = scrollView.contentSize
        textView = NSTextView(frame: NSRect(x: 0, y: 0, width: contentSize.width, height: contentSize.height))
        textView.minSize = NSSize(width: 0.0, height: contentSize.height)
        textView.maxSize = NSSize(width: CGFloat.greatestFiniteMagnitude, height: CGFloat.greatestFiniteMagnitude)
        textView.isVerticallyResizable = true
        textView.isHorizontallyResizable = false
        textView.autoresizingMask = .width
        textView.textContainer?.containerSize = NSSize(width: contentSize.width, height: CGFloat.greatestFiniteMagnitude)
        textView.textContainer?.widthTracksTextView = true
        
        // Style the text view
        textView.isEditable = false
        textView.isSelectable = true
        textView.backgroundColor = NSColor(calibratedWhite: 0.1, alpha: 0.6)
        textView.textColor = NSColor(calibratedWhite: 0.9, alpha: 1.0)
        textView.font = NSFont.monospacedSystemFont(ofSize: 13, weight: .regular)
        
        // Add padding to text view
        textView.textContainerInset = NSSize(width: 12, height: 12)
        
        // Add text view to scroll view
        scrollView.documentView = textView
        
        // Make the window key and visible
        window.makeKeyAndOrderFront(nil)
        window.orderFrontRegardless()
        NSApp.setActivationPolicy(.regular)
        NSApp.activate(ignoringOtherApps: true)
        
        // Initial text
        appendToLog("🎧 Starting Anki TTS...\n", type: .info)
        
        // Start the Python script immediately
        startPythonScript()
        
        // Setup voice recognition at the end
        setupVoiceRecognition()
    }
    
    enum LogType {
        case info
        case reading
        case error
        case waiting
    }
    
    func appendToLog(_ text: String, type: LogType = .info) {
        DispatchQueue.main.async { [weak self] in
            guard let self = self else { return }
            
            let timestamp = DateFormatter.localizedString(from: Date(), dateStyle: .none, timeStyle: .medium)
            let prefix: String
            let color: NSColor
            
            switch type {
            case .info:
                prefix = "ℹ️"
                color = NSColor(calibratedRed: 0.7, green: 0.7, blue: 1.0, alpha: 1.0)
            case .reading:
                prefix = "🔊"
                color = NSColor(calibratedRed: 0.3, green: 0.9, blue: 0.3, alpha: 1.0)
            case .error:
                prefix = "❌"
                color = NSColor(calibratedRed: 1.0, green: 0.4, blue: 0.4, alpha: 1.0)
            case .waiting:
                prefix = "⏳"
                color = NSColor(calibratedRed: 1.0, green: 0.8, blue: 0.3, alpha: 1.0)
            }
            
            let fullText = "[\(timestamp)] \(prefix) \(text)"
            let attributedString = NSAttributedString(
                string: fullText,
                attributes: [
                    .foregroundColor: color,
                    .font: NSFont.systemFont(ofSize: 14)
                ]
            )
            self.textView.textStorage?.append(attributedString)
            self.textView.scrollToEndOfDocument(nil)
            
            // Update status label
            if !text.contains("Error") {
                self.statusLabel.stringValue = text.trimmingCharacters(in: .whitespacesAndNewlines)
            }
        }
    }
    
    @objc func clearLog() {
        textView.string = ""
        appendToLog("🎧 Log cleared\n", type: .info)
    }
    
    func startPythonScript() {
        // Get the path to the Python script
        let scriptPath = findPythonScript()
        guard let scriptPath = scriptPath else {
            appendToLog("Could not find anki_tts.py\n", type: .error)
            return
        }
        
        print("Found script at: \(scriptPath)")
        
        // Create and configure the process
        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/usr/bin/env")
        process.arguments = ["poetry", "run", "python", "-u", scriptPath]
        process.currentDirectoryURL = URL(fileURLWithPath: (scriptPath as NSString).deletingLastPathComponent)
        
        // Set up pipes for both output and error
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
                    let type: LogType
                    if output.contains("Reading:") {
                        type = .reading
                    } else if output.contains("Waiting") {
                        type = .waiting
                    } else {
                        type = .info
                    }
                    self?.appendToLog("\(output)\n", type: type)
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
        ) { [weak self] notification in
            let data = errorHandle.availableData
            if !data.isEmpty {
                if let output = String(data: data, encoding: .utf8)?.trimmingCharacters(in: .whitespacesAndNewlines),
                   !output.isEmpty {
                    self?.appendToLog("\(output)\n", type: .error)
                }
                errorHandle.waitForDataInBackgroundAndNotify()
            }
        }
        
        // Start the process
        do {
            try process.run()
            pythonProcess = process
            print("Python process started")
        } catch {
            appendToLog("\(error.localizedDescription)\n", type: .error)
            print("Failed to start Python process: \(error)")
        }
    }
    
    func findPythonScript() -> String? {
        print("\nSearching for anki_tts.py...")
        print("Current directory: \(FileManager.default.currentDirectoryPath)")
        
        // Try multiple possible locations
        let possibleLocations = [
            // First try Resources directory
            FileManager.default.currentDirectoryPath + "/Resources/anki_tts.py",
            // Then try relative paths
            FileManager.default.currentDirectoryPath + "/anki_tts.py",
            FileManager.default.currentDirectoryPath + "/../Resources/anki_tts.py",
            // Try absolute path as fallback
            "/Users/lucascamillo/AnkiTTS/swift_app/Resources/anki_tts.py"
        ]
        
        print("\nChecking these locations:")
        for path in possibleLocations {
            print("Checking: \(path)")
            if FileManager.default.fileExists(atPath: path) {
                print("✅ Found Python script at: \(path)")
                return path
            }
        }
        
        print("\n❌ Could not find anki_tts.py in any location")
        return nil
    }
    
    func applicationWillTerminate(_ notification: Notification) {
        pythonProcess?.terminate()
    }
    
    @objc func showAnswer() {
        let url = URL(string: "http://127.0.0.1:8765")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let requestData: [String: Any] = [
            "action": "guiShowAnswer",
            "version": 6
        ]
        
        do {
            request.httpBody = try JSONSerialization.data(withJSONObject: requestData)
            
            URLSession.shared.dataTask(with: request) { [weak self] data, response, error in
                if let error = error {
                    self?.appendToLog("Failed to show answer: \(error.localizedDescription)\n", type: .error)
                    return
                }
                
                if let data = data,
                   let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                   let error = json["error"] as? String {
                    self?.appendToLog("Failed to show answer: \(error)\n", type: .error)
                } else {
                    DispatchQueue.main.async {
                        self?.showAnswerButton.isHidden = true
                        self?.answerButtons.forEach { $0.isHidden = false }
                    }
                    self?.appendToLog("Showing answer...\n", type: .info)
                }
            }.resume()
            
        } catch {
            appendToLog("Failed to show answer: \(error.localizedDescription)\n", type: .error)
        }
    }
    
    func answerCard(ease: Int) {
        let url = URL(string: "http://127.0.0.1:8765")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let params: [String: Any] = [
            "ease": ease
        ]
        
        let requestData: [String: Any] = [
            "action": "guiAnswerCard",
            "version": 6,
            "params": params
        ]
        
        do {
            request.httpBody = try JSONSerialization.data(withJSONObject: requestData)
            
            URLSession.shared.dataTask(with: request) { [weak self] data, response, error in
                DispatchQueue.main.async {
                    self?.showAnswerButton.isHidden = false
                    self?.answerButtons.forEach { $0.isHidden = true }
                }
                
                if let error = error {
                    self?.appendToLog("Failed to answer card: \(error.localizedDescription)\n", type: .error)
                    return
                }
                
                if let data = data,
                   let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                   let error = json["error"] as? String {
                    self?.appendToLog("Failed to answer card: \(error)\n", type: .error)
                } else {
                    self?.appendToLog("Card answered\n", type: .info)
                }
            }.resume()
            
        } catch {
            appendToLog("Failed to answer card: \(error.localizedDescription)\n", type: .error)
        }
    }
    
    @objc func answerAgain() { answerCard(ease: 1) }
    @objc func answerHard() { answerCard(ease: 2) }
    @objc func answerGood() { answerCard(ease: 3) }
    @objc func answerEasy() { answerCard(ease: 4) }
    
    func setupVoiceRecognition() {
        recognizer = NSSpeechRecognizer()
        recognizer?.commands = voiceCommands
        recognizer?.delegate = self
        recognizer?.listensInForegroundOnly = false
        recognizer?.startListening()
        appendToLog("Voice control enabled. Try saying: show, again, hard, good, easy\n", type: .info)
    }
    
    // Add window delegate method to update gradient
    func windowDidResize(_ notification: Notification) {
        if let contentView = window.contentView {
            contentView.layer?.frame = contentView.bounds
        }
    }
    
    // Add window delegate method to handle content layout
    func windowDidEndLiveResize(_ notification: Notification) {
        if let contentView = window.contentView {
            // Update button layout
            let buttonWidth: CGFloat = 120
            let spacing: CGFloat = 16
            let totalWidth = (buttonWidth * 5) + (spacing * 4)
            let startX = (contentView.frame.width - totalWidth) / 2
            
            // Update Show Answer button position
            showAnswerButton.frame.origin.x = startX
            
            // Update answer buttons positions
            for (index, button) in answerButtons.enumerated() {
                button.frame.origin.x = startX + CGFloat(index + 1) * (buttonWidth + spacing)
            }
        }
    }
}

// Add speech recognition delegate
extension AnkiTTSController: NSSpeechRecognizerDelegate {
    func speechRecognizer(_ sender: NSSpeechRecognizer, didRecognizeCommand command: String) {
        DispatchQueue.main.async { [weak self] in
            guard let self = self else { return }
            
            switch command.lowercased() {
            case "show", "show answer":
                if !self.showAnswerButton.isHidden {
                    self.showAnswer()
                }
            case "again", "repeat":
                if !self.answerButtons[0].isHidden {
                    self.answerAgain()
                }
            case "hard", "difficult":
                if !self.answerButtons[1].isHidden {
                    self.answerHard()
                }
            case "good", "okay":
                if !self.answerButtons[2].isHidden {
                    self.answerGood()
                }
            case "easy", "simple":
                if !self.answerButtons[3].isHidden {
                    self.answerEasy()
                }
            default:
                break
            }
        }
    }
}

// Create and run the application
autoreleasepool {
    let app = NSApplication.shared
    app.setActivationPolicy(.regular)
    
    let controller = AnkiTTSController()
    app.delegate = controller
    
    // Create a menu to allow proper app behavior
    let menubar = NSMenu()
    app.mainMenu = menubar
    
    // App Menu
    let appMenuItem = NSMenuItem()
    menubar.addItem(appMenuItem)
    let appMenu = NSMenu()
    appMenuItem.submenu = appMenu
    
    appMenu.addItem(NSMenuItem(title: "About Anki TTS", action: #selector(NSApplication.orderFrontStandardAboutPanel(_:)), keyEquivalent: ""))
    appMenu.addItem(NSMenuItem.separator())
    appMenu.addItem(NSMenuItem(title: "Preferences...", action: #selector(NSApplication.orderFrontStandardAboutPanel(_:)), keyEquivalent: ","))
    appMenu.addItem(NSMenuItem.separator())
    appMenu.addItem(NSMenuItem(title: "Hide Anki TTS", action: #selector(NSApplication.hide(_:)), keyEquivalent: "h"))
    let hideOthersItem = NSMenuItem(title: "Hide Others", action: #selector(NSApplication.hideOtherApplications(_:)), keyEquivalent: "h")
    hideOthersItem.keyEquivalentModifierMask = [.command, .option]
    appMenu.addItem(hideOthersItem)
    appMenu.addItem(NSMenuItem(title: "Show All", action: #selector(NSApplication.unhideAllApplications(_:)), keyEquivalent: ""))
    appMenu.addItem(NSMenuItem.separator())
    appMenu.addItem(NSMenuItem(title: "Quit Anki TTS", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q"))
    
    // Edit Menu
    let editMenuItem = NSMenuItem()
    menubar.addItem(editMenuItem)
    let editMenu = NSMenu(title: "Edit")
    editMenuItem.submenu = editMenu
    
    editMenu.addItem(NSMenuItem(title: "Copy", action: #selector(NSText.copy(_:)), keyEquivalent: "c"))
    editMenu.addItem(NSMenuItem(title: "Select All", action: #selector(NSText.selectAll(_:)), keyEquivalent: "a"))
    
    // View Menu
    let viewMenuItem = NSMenuItem()
    menubar.addItem(viewMenuItem)
    let viewMenu = NSMenu(title: "View")
    viewMenuItem.submenu = viewMenu
    
    viewMenu.addItem(NSMenuItem(title: "Clear Log", action: #selector(controller.clearLog), keyEquivalent: "k"))
    viewMenu.addItem(NSMenuItem(title: "Toggle Voice Control", action: #selector(controller.toggleVoiceControl), keyEquivalent: "v"))
    
    // Card Menu
    let cardMenuItem = NSMenuItem()
    menubar.addItem(cardMenuItem)
    let cardMenu = NSMenu(title: "Card")
    cardMenuItem.submenu = cardMenu
    
    cardMenu.addItem(NSMenuItem(title: "Show Answer", action: #selector(controller.showAnswer), keyEquivalent: "s"))
    cardMenu.addItem(NSMenuItem.separator())
    cardMenu.addItem(NSMenuItem(title: "Again", action: #selector(controller.answerAgain), keyEquivalent: "1"))
    cardMenu.addItem(NSMenuItem(title: "Hard", action: #selector(controller.answerHard), keyEquivalent: "2"))
    cardMenu.addItem(NSMenuItem(title: "Good", action: #selector(controller.answerGood), keyEquivalent: "3"))
    cardMenu.addItem(NSMenuItem(title: "Easy", action: #selector(controller.answerEasy), keyEquivalent: "4"))
    
    // Window Menu
    let windowMenuItem = NSMenuItem()
    menubar.addItem(windowMenuItem)
    let windowMenu = NSMenu(title: "Window")
    windowMenuItem.submenu = windowMenu
    
    windowMenu.addItem(NSMenuItem(title: "Minimize", action: #selector(NSWindow.miniaturize(_:)), keyEquivalent: "m"))
    windowMenu.addItem(NSMenuItem(title: "Zoom", action: #selector(NSWindow.zoom(_:)), keyEquivalent: ""))
    windowMenu.addItem(NSMenuItem.separator())
    windowMenu.addItem(NSMenuItem(title: "Bring All to Front", action: #selector(NSApplication.arrangeInFront(_:)), keyEquivalent: ""))
    
    // Help Menu
    let helpMenuItem = NSMenuItem()
    menubar.addItem(helpMenuItem)
    let helpMenu = NSMenu(title: "Help")
    helpMenuItem.submenu = helpMenu
    
    helpMenu.addItem(NSMenuItem(title: "Anki TTS Help", action: #selector(NSApplication.showHelp(_:)), keyEquivalent: "?"))
    
    app.run()
}

// Add this method to AnkiTTSController
extension AnkiTTSController {
    @objc func toggleVoiceControl() {
        if let recognizer = recognizer {
            let isListening = recognizer.delegate != nil
            if isListening {
                recognizer.stopListening()
                recognizer.delegate = nil
                appendToLog("Voice control disabled\n", type: .info)
            } else {
                recognizer.delegate = self
                recognizer.startListening()
                appendToLog("Voice control enabled\n", type: .info)
            }
        }
    }
}
