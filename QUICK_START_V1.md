# ⚡ Quick Start - AI Ultrasound Assistant V1.0

## 🎯 5-Minute Setup

### Windows (Easiest)

```bash
# 1. Extract ZIP file
# 2. Double-click: run_v1.bat
# 3. Wait for setup (~1-2 minutes)
# 4. Application starts automatically
```

### Manual Setup (if batch fails)

```bash
# 1. Install Python 3.12
#    Download: https://www.python.org/downloads/

# 2. Open Command Prompt in project folder

# 3. Create environment
python -m venv venv
venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements_v1.txt

# 5. Run application
python main_v1_complete.py
```

---

## 🎬 First Run Checklist

- [ ] **Hardware Connected**
  - [ ] Capture device plugged in
  - [ ] Ultrasound machine connected to capture device

- [ ] **Application Started**
  - [ ] No error messages
  - [ ] Main window visible

- [ ] **Devices Found**
  - [ ] Go to "Live Capture" tab
  - [ ] Click "Refresh Devices"
  - [ ] Should show at least 1 device

---

## 🎥 Live Capture - 30 Second Test

```
1. Live Capture Tab
   ↓
2. Click "Refresh Devices"
   ↓
3. Select your capture device
   ↓
4. Click "Start Capture"
   ↓
5. Video should appear on screen
   ↓
6. Click "Capture Frame"
   ↓
7. Check "AI Analysis" tab for results
```

**Expected Result**: ✅ Frame captured + AI analysis shown

---

## 🎬 Video Playback - Test with Demo Video

```
1. Download test video (or use your own):
   https://example.com/sample_ultrasound.mp4
   
2. Recorded Video Tab
   ↓
3. Click "Browse Video"
   ↓
4. Select MP4 file
   ↓
5. Click "Play"
   ↓
6. Use slider to navigate
   ↓
7. Click "Capture Frame" on interesting part
   ↓
8. Check AI Analysis results
```

---

## 👤 Patient Management - 1 Minute Setup

```
1. Patients Tab
   ↓
2. Click "New Patient"
   ↓
3. Fill in details:
   - Name: "Test Patient"
   - Age: 45
   - Gender: Male/Female
   - Contact: Any number
   
4. Click "Save Patient"
   ↓
5. Click "New Examination"
   ↓
6. Examination created and linked
```

Now all captured frames are linked to this patient!

---

## 🤖 AI Analysis - Understanding Results

### **Detected Organs Tab**
Shows all organs found in frame:

```
Organ Name  | Confidence | Quality | Status
------------|------------|---------|--------
Liver       | 92.5%      | Good    | ✓ Best
Kidney L    | 87.3%      | Good    |
Pancreas    | 78.9%      | Fair    |
```

**What it means:**
- **Confidence**: How sure AI is (higher = better)
- **Quality**: Image quality level
- **Status**: ⭐ if best frame so far

### **Quality Metrics**
```
Image Quality:     [████████░] 87% - EXCELLENT
Frame Score:       [██████░░░] 75% - GOOD ⭐ BEST FRAME
```

**Quality Levels:**
- 🟢 **Excellent** (85-100) - Perfect for diagnosis
- 🟡 **Good** (70-85) - Acceptable
- 🟠 **Fair** (55-70) - Marginal, consider recapture
- 🔴 **Poor** (<55) - Recapture needed

### **Recommendations**
If quality is low, you'll see tips like:
- "Image is blurry, adjust transducer position"
- "Low contrast, increase gain settings"
- "High noise detected, check probe connection"

---

## 🗄️ Data Storage - Where Everything Goes

```
Project Folder/
├── captures/
│   └── 20250106_143052_F000001.jpg     ← Captured frames
│
├── ultrasound.db                        ← Patient/exam data
│
├── logs/
│   └── ultrasound.log                   ← Detailed logs
│
└── settings.json                        ← Your preferences
```

All patient data saved locally in database!

---

## ⚙️ Settings - Customize Your Experience

**Settings Tab → Adjust:**

```
Window Size       → Width/Height
Resolution        → 640x480, 1024x768, 1280x720
Target FPS        → 15, 30 (higher = smoother)
GPU Acceleration  → Enable if you have NVIDIA GPU
```

All settings auto-saved!

---

## 🆘 Troubleshooting - Quick Fixes

### **"No devices found"**
```
✅ Solution:
1. Unplug USB capture device
2. Wait 5 seconds
3. Plug back in
4. Click "Refresh Devices"
5. Try different USB port
```

### **Video won't play**
```
✅ Solution:
1. Check file format (MP4, AVI, MKV, MOV)
2. Try converting to MP4:
   ffmpeg -i video.avi -c:v libx264 output.mp4
3. Verify file not corrupted (open in VLC)
```

### **Slow/Laggy**
```
✅ Solution:
1. Reduce resolution: 1280x720 → 640x480
2. Lower FPS: 30 → 15
3. Close other applications
4. Disable "Show FPS" in settings
```

### **Application crashes**
```
✅ Solution:
1. Check logs/ultrasound.log
2. Reinstall dependencies:
   pip install --upgrade -r requirements_v1.txt
3. Restart application
4. Try with test video first
```

---

## 📊 V1.0 Features Summary

| Feature | Status | How to Use |
|---------|--------|-----------|
| Live Capture | ✅ | Live Capture tab |
| Video Playback | ✅ | Recorded Video tab |
| Organ Detection | ✅ | Automatic when capturing |
| Quality Assessment | ✅ | AI Analysis tab |
| Best Frame Selection | ✅ | ⭐ auto-marked |
| Patient Management | ✅ | Patients tab |
| Exam Tracking | ✅ | New Examination button |
| Database Storage | ✅ | Automatic |
| AI Reports | ✅ | Analysis tab |

---

## 🔄 Typical Workflow

### **Scenario 1: Live Ultrasound**
```
1. Connect patient
2. Select capture device
3. Start capture
4. Scan abdomen
5. Capture best frames (press button when ready)
6. Review AI analysis
7. Save patient + exam (automatic)
```

### **Scenario 2: Review Recording**
```
1. Load ultrasound video file
2. Play through sequence
3. Pause on important moments
4. Capture frames for analysis
5. AI analyzes automatically
6. Compare quality across frames
7. Select best 5 frames
```

### **Scenario 3: Quality Control**
```
1. Capture multiple frames
2. Check AI quality scores
3. Follow recommendations for improvement
4. Recapture if needed
5. Compare before/after
6. Best frame automatically selected
```

---

## 📞 Getting Help

### **Check Logs**
```bash
# Open logs folder
logs/ultrasound.log

# Last 50 lines:
tail -50 logs/ultrasound.log
```

### **Common Error Messages**

| Error | Cause | Solution |
|-------|-------|----------|
| `ModuleNotFoundError: PySide6` | Missing dependency | `pip install -r requirements_v1.txt` |
| `Cannot open capture device` | Device not found | Unplug/replug USB |
| `Database locked` | Corrupted DB | Delete `ultrasound.db-journal` |
| `CUDA not available` | GPU not found | Set `enable_gpu: false` |

---

## 🚀 Next Steps After Setup

1. **Run with test video**
   - Test all features without hardware

2. **Connect capture device**
   - Start with short 30-second capture

3. **Create test patient**
   - Practice workflow

4. **Review AI outputs**
   - Understand detection confidence levels

5. **Adjust settings**
   - Find optimal resolution/FPS

6. **Read full README**
   - Understand advanced features

---

## 💡 Pro Tips

### **Tip 1: Keyboard Shortcuts**
```
Space       → Capture frame
P           → Pause/Play video
S           → Stop capture
R           → Refresh devices
```

### **Tip 2: Quality Optimization**
- Start with 640x480 resolution
- Graduallt increase if performance good
- 30 FPS = smoother but needs more CPU

### **Tip 3: Database Backup**
- `ultrasound.db` contains all patient data
- Backup regularly:
  ```
  copy ultrasound.db backup_$(date).db
  ```

### **Tip 4: Batch Processing**
- Can process many videos in sequence
- Load video → capture frames → move to next video

---

## ✅ Verification Checklist

After setup, verify each component:

- [ ] **Python & Dependencies**
  ```bash
  python --version        # Should be 3.12+
  pip show PySide6        # Should show version
  pip show opencv-python  # Should show version
  ```

- [ ] **Application Starts**
  ```bash
  python main_v1_complete.py
  # Window should open
  ```

- [ ] **Database Working**
  - Patients Tab → New Patient
  - Should save without errors

- [ ] **Video Processing**
  - Recorded Video Tab → Browse video
  - Should play smoothly

- [ ] **AI Analysis**
  - Capture frame
  - Should show analysis in tab

---

## 🎓 Learning Resources

### **Video Tutorials** (Coming in V1.1)
- Installation walkthrough
- Live capture demo
- AI analysis explained
- Database management

### **Documentation**
- Full README: `README_V1.md`
- Architecture: `ARCHITECTURE_V1.md`
- API Reference: `API_REFERENCE.md`

### **Example Workflows**
- See `examples/` folder
- Python notebooks showing usage

---

## 📈 Version Info

**Current Version**: V1.0  
**Release Date**: January 2025  
**Status**: ✅ Production Ready  
**Next Update**: V1.1 (March 2025)

---

**Ready to start?** → Run `run_v1.bat` now! 🚀

