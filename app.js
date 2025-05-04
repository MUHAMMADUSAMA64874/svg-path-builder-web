class SVGPathBuilder {
    constructor() {
        this.canvas = document.getElementById('drawing-canvas');
        this.ctx = this.canvas.getContext('2d');
        this.svgCodeTextarea = document.getElementById('svg-code');
        this.statusBar = document.getElementById('status-bar');
        
        // Initialize state
        this.points = [];
        this.undoStack = [];
        this.redoStack = [];
        this.dragging = false;
        this.selectedPointIndex = null;
        this.isAnimating = false;
        this.animationId = null;
        this.image = null;
        this.imageObject = null;
        
        // Canvas settings
        this.canvasWidth = this.canvas.width;
        this.canvasHeight = this.canvas.height;
        this.animationSpeed = 0.05; // Seconds per frame
        
        // Default values
        this.currentMode = 'add_points';
        this.textContent = 'Your text here';
        this.fontSize = 36;
        this.textColor = '#000000';
        this.letterSpacing = 0;
        this.startOffset = 0;
        this.duration = 10;
        
        // Initialize UI
        this.setupEventListeners();
        this.updateUIFromState();
        this.drawPath();
    }
    
    setupEventListeners() {
        // Mode selection
        document.querySelectorAll('input[name="mode"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.currentMode = e.target.value;
            });
        });
        
        // Canvas interactions
        this.canvas.addEventListener('mousedown', this.handleCanvasClick.bind(this));
        this.canvas.addEventListener('mousemove', this.handleCanvasDrag.bind(this));
        this.canvas.addEventListener('mouseup', this.handleCanvasRelease.bind(this));
        this.canvas.addEventListener('mouseleave', this.handleCanvasRelease.bind(this));
        
        // Text properties
        document.getElementById('text-content').addEventListener('input', (e) => {
            this.textContent = e.target.value;
            this.drawPath();
        });
        
        document.getElementById('font-size').addEventListener('input', (e) => {
            this.fontSize = parseInt(e.target.value);
            this.drawPath();
        });
        
        document.getElementById('text-color').addEventListener('input', (e) => {
            this.textColor = e.target.value;
            this.drawPath();
        });
        
        document.getElementById('letter-spacing').addEventListener('input', (e) => {
            this.letterSpacing = parseInt(e.target.value);
            document.getElementById('spacing-value').textContent = this.letterSpacing;
            this.drawPath();
        });
        
        document.getElementById('start-offset').addEventListener('input', (e) => {
            this.startOffset = parseInt(e.target.value);
            document.getElementById('offset-value').textContent = this.startOffset;
            this.drawPath();
        });
        
        document.getElementById('duration').addEventListener('input', (e) => {
            this.duration = parseInt(e.target.value);
        });
        
        // Path controls
        document.getElementById('load-path').addEventListener('click', () => {
            this.loadPathData(document.getElementById('path-data').value);
        });
        
        document.getElementById('sample-path').addEventListener('click', () => {
            document.getElementById('path-data').value = "M63,766 C55,25 776,782 775,38";
            this.letterSpacing = -2;
            document.getElementById('letter-spacing').value = -2;
            document.getElementById('spacing-value').textContent = -2;
            this.fontSize = 18;
            document.getElementById('font-size').value = 18;
            this.textContent = "Thank You 😉";
            document.getElementById('text-content').value = "Thank You 😉";
            this.loadPathData(document.getElementById('path-data').value);
        });
        
        // Action buttons
        document.getElementById('clear-canvas').addEventListener('click', () => {
            this.clearCanvas();
        });
        
        document.getElementById('toggle-animation').addEventListener('click', () => {
            this.toggleAnimation();
        });
        
        // Export/Import buttons
        document.getElementById('save-svg').addEventListener('click', () => {
            this.saveSVGFile();
        });
        
        document.getElementById('load-svg').addEventListener('click', () => {
            this.loadSVGFile();
        });
        
        document.getElementById('copy-svg').addEventListener('click', () => {
            this.copySVGCode();
        });
        
        document.getElementById('load-image').addEventListener('click', () => {
            this.loadImage();
        });
        
        document.getElementById('fit-to-canvas').addEventListener('click', () => {
            this.fitToCanvas();
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch (e.key.toLowerCase()) {
                    case 'z':
                        this.undo();
                        e.preventDefault();
                        break;
                    case 'y':
                        this.redo();
                        e.preventDefault();
                        break;
                    case 's':
                        this.saveSVGFile();
                        e.preventDefault();
                        break;
                }
            }
        });
    }
    
    updateUIFromState() {
        document.getElementById('text-content').value = this.textContent;
        document.getElementById('font-size').value = this.fontSize;
        document.getElementById('text-color').value = this.textColor;
        document.getElementById('letter-spacing').value = this.letterSpacing;
        document.getElementById('spacing-value').textContent = this.letterSpacing;
        document.getElementById('start-offset').value = this.startOffset;
        document.getElementById('offset-value').textContent = this.startOffset;
        document.getElementById('duration').value = this.duration;
    }
    
    handleCanvasClick(e) {
        const rect = this.canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        if (this.currentMode === 'add_points') {
            this.saveState();
            if (this.points.length === 0) {
                this.points.push(['M', x, y]);
            } else {
                const [lastX, lastY] = this.getPreviousEndpoint(this.points.length);
                const cp1X = lastX + (x - lastX) / 3;
                const cp1Y = lastY + (y - lastY) / 3;
                const cp2X = lastX + 2 * (x - lastX) / 3;
                const cp2Y = lastY + 2 * (y - lastY) / 3;
                this.points.push(['C', cp1X, cp1Y, cp2X, cp2Y, x, y]);
            }
            this.drawPath();
        } else if (this.currentMode === 'edit_points') {
            for (let i = 0; i < this.points.length; i++) {
                const point = this.points[i];
                if (point[0] === 'M') {
                    const px = point[1];
                    const py = point[2];
                    if (Math.hypot(x - px, y - py) < 10) {
                        this.selectedPointIndex = [i, 0];
                        this.dragging = true;
                        return;
                    }
                } else if (point[0] === 'C') {
                    for (let j = 0; j < 3; j++) {
                        const px = point[1 + j * 2];
                        const py = point[2 + j * 2];
                        if (Math.hypot(x - px, y - py) < 10) {
                            this.selectedPointIndex = [i, j];
                            this.dragging = true;
                            return;
                        }
                    }
                }
            }
        }
    }
    
    handleCanvasDrag(e) {
        if (!this.dragging || this.selectedPointIndex === null) return;
        
        const rect = this.canvas.getBoundingClientRect();
        const x = Math.max(0, Math.min(e.clientX - rect.left, this.canvasWidth));
        const y = Math.max(0, Math.min(e.clientY - rect.top, this.canvasHeight));
        
        const [idx, pointType] = this.selectedPointIndex;
        
        this.saveState();
        if (idx < this.points.legth) {
            const point = this.points[idx];
            if (point[0] === 'M') {
                this.points[idx] = ['M', x, y];
            } else if (point[0] === 'C' && pointType < 3) {
                const newPoint = [...point];
                newPoint[1 + pointType * 2] = x;
                newPoint[2 + pointType * 2] = y;
                this.points[idx] = newPoint;
            }
            this.drawPath();
        }
    }
    
    handleCanvasRelease() {
        this.dragging = false;
        this.selectedPointIndex = null;
        this.drawPath();
    }
    
    saveState() {
        this.undoStack.push(JSON.parse(JSON.stringify(this.points)));
        this.redoStack = [];
        if (this.undoStack.length > 50) {
            this.undoStack.shift();
        }
    }
    
    undo() {
        if (this.undoStack.length > 0) {
            this.redoStack.push(JSON.parse(JSON.stringify(this.points)));
            this.points = JSON.parse(JSON.stringify(this.undoStack.pop()));
            this.drawPath();
            this.showStatus("Undo successful!");
        }
    }
    
    redo() {
        if (this.redoStack.length > 0) {
            this.undoStack.push(JSON.parse(JSON.stringify(this.points)));
            this.points = JSON.parse(JSON.stringify(this.redoStack.pop()));
            this.drawPath();
            this.showStatus("Redo successful!");
        }
    }
    
    getPreviousEndpoint(index) {
        if (index <= 0) return [0, 0];
        const prev = this.points[index - 1];
        return prev[0] === 'M' ? [prev[1], prev[2]] : [prev[5], prev[6]];
    }
    
    drawPath() {
        // Clear canvas
        this.ctx.clearRect(0, 0, this.canvasWidth, this.canvasHeight);
        
        // Draw image if present
        if (this.imageObject) {
            this.ctx.drawImage(this.imageObject, 0, 0);
        }
        
        // Draw path
        if (this.points.length === 0) {
            this.generateSVG();
            return;
        }
        
        // Draw the curve
        this.ctx.beginPath();
        if (this.points[0][0] === 'M') {
            this.ctx.moveTo(this.points[0][1], this.points[0][2]);
        }
        
        for (let i = 1; i < this.points.length; i++) {
            if (this.points[i][0] === 'C') {
                const cp1x = this.points[i][1];
                const cp1y = this.points[i][2];
                const cp2x = this.points[i][3];
                const cp2y = this.points[i][4];
                const endX = this.points[i][5];
                const endY = this.points[i][6];
                
                this.ctx.bezierCurveTo(cp1x, cp1y, cp2x, cp2y, endX, endY);
            }
        }
        
        this.ctx.strokeStyle = 'black';
        this.ctx.lineWidth = 2;
        this.ctx.stroke();
        
        // Draw points and control handles
        for (let i = 0; i < this.points.length; i++) {
            const point = this.points[i];
            if (point[0] === 'M') {
                const x = point[1];
                const y = point[2];
                
                // Draw point
                this.ctx.beginPath();
                this.ctx.arc(x, y, 5, 0, Math.PI * 2);
                this.ctx.fillStyle = 'blue';
                this.ctx.fill();
                
                // Draw label
                this.ctx.fillStyle = 'black';
                this.ctx.font = '12px Arial';
                this.ctx.fillText(`M${i}`, x, y - 15);
            } else if (point[0] === 'C') {
                const cp1x = point[1];
                const cp1y = point[2];
                const cp2x = point[3];
                const cp2y = point[4];
                const endX = point[5];
                const endY = point[6];
                
                // Draw control points
                this.ctx.beginPath();
                this.ctx.arc(cp1x, cp1y, 4, 0, Math.PI * 2);
                this.ctx.fillStyle = 'red';
                this.ctx.fill();
                
                this.ctx.beginPath();
                this.ctx.arc(cp2x, cp2y, 4, 0, Math.PI * 2);
                this.ctx.fillStyle = 'green';
                this.ctx.fill();
                
                // Draw end point
                this.ctx.beginPath();
                this.ctx.arc(endX, endY, 5, 0, Math.PI * 2);
                this.ctx.fillStyle = 'blue';
                this.ctx.fill();
                
                // Draw control lines
                if (i > 0) {
                    const [prevX, prevY] = this.getPreviousEndpoint(i);
                    
                    this.ctx.beginPath();
                    this.ctx.moveTo(prevX, prevY);
                    this.ctx.lineTo(cp1x, cp1y);
                    this.ctx.strokeStyle = 'red';
                    this.ctx.setLineDash([2, 2]);
                    this.ctx.stroke();
                    this.ctx.setLineDash([]);
                    
                    this.ctx.beginPath();
                    this.ctx.moveTo(endX, endY);
                    this.ctx.lineTo(cp2x, cp2y);
                    this.ctx.strokeStyle = 'green';
                    this.ctx.setLineDash([2, 2]);
                    this.ctx.stroke();
                    this.ctx.setLineDash([]);
                }
                
                // Draw labels
                this.ctx.fillStyle = 'black';
                this.ctx.font = '12px Arial';
                this.ctx.fillText(`CP1.${i}`, cp1x, cp1y - 10);
                this.ctx.fillText(`CP2.${i}`, cp2x, cp2y - 10);
                this.ctx.fillText(`P${i}`, endX, endY - 15);
            }
        }
        
        // Draw text preview if not animating
        if (!this.isAnimating && this.textContent) {
            const pathPoints = this.samplePathPoints(100);
            if (pathPoints.length > 0) {
                const startOffsetIdx = Math.max(0, Math.min(
                    Math.floor(pathPoints.length * this.startOffset / 100),
                    pathPoints.length - 1
                ));
                
                const charWidth = this.fontSize * 0.6;
                let currentPos = startOffsetIdx;
                
                this.ctx.font = `${this.fontSize}px Arial`;
                this.ctx.fillStyle = this.textColor;
                this.ctx.textAlign = 'center';
                this.ctx.textBaseline = 'middle';
                
                for (const char of this.textContent) {
                    if (currentPos >= pathPoints.length) break;
                    const [x, y] = pathPoints[currentPos];
                    this.ctx.fillText(char, x, y);
                    currentPos += Math.round(charWidth + this.letterSpacing);
                }
            }
        }
        
        this.generateSVG();
    }
    
    samplePathPoints(numPoints) {
        const pathPoints = [];
        if (this.points.length === 0) return pathPoints;
        
        if (this.points[0][0] === 'M') {
            pathPoints.push([this.points[0][1], this.points[0][2]]);
        }
        
        for (let i = 1; i < this.points.length; i++) {
            if (this.points[i][0] === 'C') {
                const [prevX, prevY] = this.getPreviousEndpoint(i);
                const cp1x = this.points[i][1];
                const cp1y = this.points[i][2];
                const cp2x = this.points[i][3];
                const cp2y = this.points[i][4];
                const endX = this.points[i][5];
                const endY = this.points[i][6];
                
                const pointsPerSegment = Math.floor(numPoints / Math.max(1, this.points.length - 1));
                for (let j = 1; j <= pointsPerSegment; j++) {
                    const t = j / pointsPerSegment;
                    const x = Math.pow(1-t, 3) * prevX + 3 * Math.pow(1-t, 2) * t * cp1x + 
                              3 * (1-t) * Math.pow(t, 2) * cp2x + Math.pow(t, 3) * endX;
                    const y = Math.pow(1-t, 3) * prevY + 3 * Math.pow(1-t, 2) * t * cp1y + 
                              3 * (1-t) * Math.pow(t, 2) * cp2y + Math.pow(t, 3) * endY;
                    pathPoints.push([x, y]);
                }
            }
        }
        
        return pathPoints;
    }
    
    generateSVG() {
        if (this.points.length === 0) {
            this.svgCodeTextarea.value = "No path defined yet.";
            return;
        }
        
        try {
            // Generate path data
            let pathData = [];
            for (const point of this.points) {
                if (point[0] === 'M') {
                    pathData.push(`M${point[1].toFixed(2)},${point[2].toFixed(2)}`);
                } else if (point[0] === 'C') {
                    pathData.push(
                        `C${point[1].toFixed(2)},${point[2].toFixed(2)} ` +
                        `${point[3].toFixed(2)},${point[4].toFixed(2)} ` +
                        `${point[5].toFixed(2)},${point[6].toFixed(2)}`
                    );
                }
            }
            
            // Calculate viewBox
            const allX = [];
            const allY = [];
            
            for (const point of this.points) {
                if (point[0] === 'M') {
                    allX.push(point[1]);
                    allY.push(point[2]);
                } else if (point[0] === 'C') {
                    allX.push(point[1], point[3], point[5]);
                    allY.push(point[2], point[4], point[6]);
                }
            }
            
            const minX = Math.min(...allX);
            const maxX = Math.max(...allX);
            const minY = Math.min(...allY);
            const maxY = Math.max(...allY);
            
            const viewBox = `${(minX-50).toFixed(2)} ${(minY-50).toFixed(2)} ${(maxX-minX+100).toFixed(2)} ${(maxY-minY+100).toFixed(2)}`;
            
            // Generate SVG code
            const svgCode = `<svg xmlns="http://www.w3.org/2000/svg" 
viewBox="${viewBox}" 
width="100%" 
height="100%">
    <path id="curve" 
        d="${pathData.join(' ')}" 
        fill="none" 
        stroke="black" 
        stroke-width="2"/>
    <text font-size="${this.fontSize}" 
        fill="${this.textColor}" 
        letter-spacing="${this.letterSpacing}px">
        <textPath href="#curve" 
            startOffset="${this.startOffset}%">
            ${this.textContent.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')}
            <animate 
                attributeName="startOffset" 
                from="100%" 
                to="-100%" 
                dur="${this.duration}s" 
                repeatCount="indefinite"/>
        </textPath>
    </text>
</svg>`;
            
            this.svgCodeTextarea.value = svgCode;
        } catch (error) {
            this.svgCodeTextarea.value = `Error generating SVG: ${error.message}`;
        }
    }
    
    loadPathData(pathString) {
        try {
            pathString = pathString.trim();
            if (!pathString) return;
            
            this.saveState();
            this.points = [];
            let currentX = 0, currentY = 0;
            
            // Tokenize the path string
            const tokens = [];
            let i = 0;
            while (i < pathString.length) {
                const char = pathString[i];
                if (/[A-Za-z]/.test(char)) {
                    tokens.push(char);
                    i++;
                } else if (/[\s,]/.test(char)) {
                    i++;
                    continue;
                } else {
                    const numMatch = /[+-]?\d*\.?\d+(?:[eE][+-]?\d+)?/.exec(pathString.slice(i));
                    if (numMatch) {
                        tokens.push(numMatch[0]);
                        i += numMatch[0].length;
                    } else {
                        throw new Error(`Invalid character at position ${i}: ${char}`);
                    }
                }
            }
            
            i = 0;
            while (i < tokens.length) {
                const cmd = tokens[i];
                i++;
                
                if (cmd.toLowerCase() === 'm') {
                    if (i + 1 >= tokens.length) {
                        throw new Error("Incomplete 'M'/'m' command");
                    }
                    let x = parseFloat(tokens[i]);
                    let y = parseFloat(tokens[i + 1]);
                    if (cmd === 'm') {
                        x += currentX;
                        y += currentY;
                    }
                    this.points.push(['M', x, y]);
                    currentX = x;
                    currentY = y;
                    i += 2;
                    
                    while (i < tokens.length && !/[A-Za-z]/.test(tokens[i])) {
                        if (i + 1 >= tokens.length) {
                            throw new Error("Incomplete implicit line-to command");
                        }
                        x = parseFloat(tokens[i]);
                        y = parseFloat(tokens[i + 1]);
                        if (cmd === 'm') {
                            x += currentX;
                            y += currentY;
                        }
                        const cp1x = currentX + (x - currentX) / 3;
                        const cp1y = currentY + (y - currentY) / 3;
                        const cp2x = currentX + 2 * (x - currentX) / 3;
                        const cp2y = currentY + 2 * (y - currentY) / 3;
                        this.points.push(['C', cp1x, cp1y, cp2x, cp2y, x, y]);
                        currentX = x;
                        currentY = y;
                        i += 2;
                    }
                } else if (cmd.toLowerCase() === 'c') {
                    while (i < tokens.length && !/[A-Za-z]/.test(tokens[i])) {
                        if (i + 5 >= tokens.length) {
                            throw new Error("Incomplete 'C'/'c' command");
                        }
                        let cp1x = parseFloat(tokens[i]);
                        let cp1y = parseFloat(tokens[i + 1]);
                        let cp2x = parseFloat(tokens[i + 2]);
                        let cp2y = parseFloat(tokens[i + 3]);
                        let endX = parseFloat(tokens[i + 4]);
                        let endY = parseFloat(tokens[i + 5]);
                        
                        if (cmd === 'c') {
                            cp1x += currentX;
                            cp1y += currentY;
                            cp2x += currentX;
                            cp2y += currentY;
                            endX += currentX;
                            endY += currentY;
                        }
                        
                        this.points.push(['C', cp1x, cp1y, cp2x, cp2y, endX, endY]);
                        currentX = endX;
                        currentY = endY;
                        i += 6;
                    }
                } else if (cmd.toLowerCase() === 'z') {
                    continue;
                } else {
                    throw new Error(`Unsupported path command: ${cmd}`);
                }
            }
            
            if (this.points.length > 0) {
                this.normalizePath();
                this.drawPath();
                this.showStatus("Path loaded successfully!");
            } else {
                throw new Error("No valid path commands found");
            }
        } catch (error) {
            this.showStatus(`Error loading path: ${error.message}`, "error");
            this.svgCodeTextarea.value = `Error loading path: ${error.message}`;
        }
    }
    
    normalizePath() {
        if (this.points.length === 0) return;
        
        const allX = [];
        const allY = [];
        
        for (const point of this.points) {
            if (point[0] === 'M') {
                allX.push(point[1]);
                allY.push(point[2]);
            } else if (point[0] === 'C') {
                allX.push(point[1], point[3], point[5]);
                allY.push(point[2], point[4], point[6]);
            }
        }
        
        const minX = Math.min(...allX);
        const maxX = Math.max(...allX);
        const minY = Math.min(...allY);
        const maxY = Math.max(...allY);
        
        const width = maxX - minX || 1;
        const height = maxY - minY || 1;
        
        const padding = 50;
        const widthScale = (this.canvasWidth - 2 * padding) / width;
        const heightScale = (this.canvasHeight - 2 * padding) / height;
        const scale = Math.min(widthScale, heightScale);
        
        const offsetX = (this.canvasWidth - width * scale) / 2 - minX * scale;
        const offsetY = (this.canvasHeight - height * scale) / 2 - minY * scale;
        
        for (let i = 0; i < this.points.length; i++) {
            const point = this.points[i];
            if (point[0] === 'M') {
                this.points[i] = ['M', point[1] * scale + offsetX, point[2] * scale + offsetY];
            } else if (point[0] === 'C') {
                this.points[i] = [
                    'C',
                    point[1] * scale + offsetX,
                    point[2] * scale + offsetY,
                    point[3] * scale + offsetX,
                    point[4] * scale + offsetY,
                    point[5] * scale + offsetX,
                    point[6] * scale + offsetY
                ];
            }
        }
    }
    
    fitToCanvas() {
        this.saveState();
        this.normalizePath();
        this.drawPath();
        this.showStatus("Path fitted to canvas!");
    }
    
    clearCanvas() {
        if (this.points.length > 0) {
            this.saveState();
        }
        this.points = [];
        this.image = null;
        this.imageObject = null;
        this.isAnimating = false;
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
            this.animationId = null;
        }
        this.ctx.clearRect(0, 0, this.canvasWidth, this.canvasHeight);
        this.svgCodeTextarea.value = "";
        this.drawPath();
        this.showStatus("Canvas cleared!");
    }
    
    loadImage() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = 'image/png,image/jpeg,image/bmp';
        input.onchange = (e) => {
            const file = e.target.files[0];
            if (file) {
                const img = new Image();
                img.onload = () => {
                    const scale = Math.min(this.canvasWidth / img.width, this.canvasHeight / img.height);
                    const newWidth = img.width * scale;
                    const newHeight = img.height * scale;
                    this.imageObject = new Image();
                    this.imageObject.src = img.src;
                    this.imageObject.width = newWidth;
                    this.imageObject.height = newHeight;
                    this.drawPath();
                    this.showStatus("Image loaded successfully!");
                };
                img.onerror = () => {
                    this.showStatus("Failed to load image", "error");
                };
                img.src = URL.createObjectURL(file);
            }
        };
        input.click();
    }
    
    saveSVGFile() {
        const svgCode = this.svgCodeTextarea.value;
        if (!svgCode || svgCode.includes("No path defined") || svgCode.includes("Error generating")) {
            this.showStatus("No valid SVG to save!", "error");
            return;
        }
        const blob = new Blob([svgCode], { type: 'image/svg+xml' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'path.svg';
        a.click();
        URL.revokeObjectURL(url);
        this.showStatus("SVG saved successfully!");
    }
    
    loadSVGFile() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.svg';
        input.onchange = (e) => {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = (event) => {
                    const content = event.target.result;
                    const pathMatch = content.match(/<path[^>]*d="([^"]+)"/);
                    if (pathMatch) {
                        document.getElementById('path-data').value = pathMatch[1];
                        this.loadPathData(pathMatch[1]);
                    } else {
                        this.showStatus("No valid path data found in SVG file", "error");
                    }
                };
                reader.onerror = () => {
                    this.showStatus("Failed to load SVG file", "error");
                };
                reader.readAsText(file);
            }
        };
        input.click();
    }
    
    copySVGCode() {
        const svgCode = this.svgCodeTextarea.value;
        if (!svgCode || svgCode.includes("No path defined") || svgCode.includes("Error generating")) {
            this.showStatus("No valid SVG code to copy!", "error");
            return;
        }
        navigator.clipboard.writeText(svgCode).then(() => {
            this.showStatus("SVG code copied to clipboard!");
        }).catch((err) => {
            this.showStatus(`Failed to copy SVG code: ${err.message}`, "error");
        });
    }
    
    toggleAnimation() {
        this.isAnimating = !this.isAnimating;
        const button = document.getElementById('toggle-animation');
        button.innerHTML = this.isAnimating
            ? '<i class="fas fa-stop"></i> Stop Animation'
            : '<i class="fas fa-play"></i> Preview Animation';
        if (this.isAnimating) {
            this.animateText();
        } else if (this.animationId) {
            cancelAnimationFrame(this.animationId);
            this.animationId = null;
            this.drawPath();
        }
    }
    
    animateText() {
        if (!this.isAnimating) return;
        
        const pathPoints = this.samplePathPoints(200);
        if (!pathPoints.length || !this.textContent) {
            this.animationId = requestAnimationFrame(this.animateText.bind(this));
            return;
        }
        
        this.ctx.clearRect(0, 0, this.canvasWidth, this.canvasHeight);
        
        if (this.imageObject) {
            this.ctx.drawImage(this.imageObject, 0, 0);
        }
        
        this.drawPath();
        
        const currentTime = performance.now() / 1000;
        const progress = (currentTime % this.duration) / this.duration;
        const startOffsetIdx = Math.floor(pathPoints.length * (1 - progress));
        const charWidth = this.fontSize * 0.6;
        let currentPos = startOffsetIdx;
        
        this.ctx.font = `${this.fontSize}px Arial`;
        this.ctx.fillStyle = this.textColor;
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'middle';
        
        for (const char of this.textContent) {
            if (currentPos >= pathPoints.length || currentPos < 0) continue;
            const [x, y] = pathPoints[currentPos];
            this.ctx.fillText(char, x, y);
            currentPos += Math.round(charWidth + this.letterSpacing);
        }
        
        this.animationId = requestAnimationFrame(this.animateText.bind(this));
    }
    
    showStatus(message, type = "success") {
        this.statusBar.textContent = message;
        this.statusBar.className = `status-bar show ${type}`;
        setTimeout(() => {
            this.statusBar.className = 'status-bar';
        }, 2000);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new SVGPathBuilder();
});