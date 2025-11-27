# **MapZ**
### **Mili-Tac Map for DayZ using Python**

![Dashboard](https://raw.githubusercontent.com/Pandora401/MapZ/refs/heads/main/Assets/Screenshots/Updates.PNG)

![Dashboard](https://raw.githubusercontent.com/Pandora401/MapZ/refs/heads/main/Assets/Screenshots/Capture.PNG)

MapZ is a fully interactive, Pygame-based tactical mapping system inspired by military-style HUDs in DayZ and other survival games.  
It renders multi-tile world maps, supports smooth zooming focused on the mouse cursor, and includes dual-map HUD views, crosshairs, filters, and comment interaction features.

This tool is perfect for:
- Gameplay utilities  
- Reconnaissance & tactical planning  
- Modding / developer tools  
- UI/UX prototyping  
- Python game development learning  

---

## **✨ Key Features**

### 🗺️ **Tile-Based Map Rendering**
- Loads large maps from 256×256 tile sets.  
- Missing tiles show a **grey fallback** tile with X/Y tile coordinates.  
- Fully resizable window + fullscreen support.  

### 🔍 **Advanced Zoom & Camera**
- Smooth zoom (2× to 8×) centered exactly on the **mouse pointer**.  
- Click-and-drag panning with boundary clamping so you never leave the map.  
- Interpolated zoom system for smooth visual transitions.  

### 🖥️ **Dual Map HUD System**
#### **Large Main Map**
- Always ~40% more zoomed-in than the minimap.  
- Displays a **segmented square crosshair** (“frame-style”) with corner gaps.

#### **Mini-Map**
- Circular crosshair in the center.  
- Mirrors main-map position & zoom (scaled).  
- Great for tactical overview.

### 🎛️ **Optional Filters**
- Invert mode (global or per-map).  
- Tint overlays.  
- Customizable HUD styling & colors.

---

## **📝 Interactive Comment System**
- Click coordinates inside comments → main map jumps to that location.  
- On hover:
  - Underline
  - Pointer cursor  
- Comment bar behavior:
  - `>` is **always yellow**  
  - Placeholder “Write comment” is **dark grey**  
  - Typed text is **yellow**  

---

## **📸 Variations**

### **Variation 1**
![Dashboard](https://raw.githubusercontent.com/Pandora401/MapZ/refs/heads/main/Assets/Screenshots/dash1.PNG)

### **Mini Map Variation**
![Dashboard](https://raw.githubusercontent.com/Pandora401/MapZ/refs/heads/main/Assets/Screenshots/simpleMap.PNG)

### **Snatcher Script (iSurvive)**
![Dashboard](https://raw.githubusercontent.com/Pandora401/MapZ/refs/heads/main/Assets/Screenshots/snatcher.PNG)

---

## **🗂️ Project Structure**

MapZ/
│
├── dash.py
├── map.py
├── tiles/
├── Assets/
│ └── Screenshots/
├── README.md
└── requirements.txt # Yet to include
