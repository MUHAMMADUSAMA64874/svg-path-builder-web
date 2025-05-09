SVG Path Builder

A web-based tool for creating and editing SVG paths with Bezier curves, text along paths, and animations. The application provides an intuitive interface for designing complex SVG paths, with features like grid snapping, color customization, dark mode, and responsive canvas scaling.
🔗 Live Demo: SVG Path Builder
Table of Contents

Features
Installation
Usage
Contributing
License

Features

Interactive Path Creation: Add and edit points to create SVG paths with Move (M) and Cubic Bezier (C) commands.
Text Along Path: Add customizable text that follows the path, with options for font size, color, letter spacing, and start offset.
Animation: Preview text animations along the path with adjustable duration and direction (left-to-right or right-to-left).
Color Customization: Change colors for the path, endpoints, control points, and handles via color pickers.
Dark Mode: Toggle between light and dark themes for better visibility, with enhanced dot contrast in dark mode.
Responsive Canvas: The SVG canvas scales dynamically to fit different screen sizes while maintaining a 800x600 viewBox.
Grid Controls: Toggle grid visibility, adjust grid size (10–100px), and enable snapping for precise point placement.
Import/Export: Load SVG files, save SVG output, copy SVG code to clipboard, or load images for tracing.
Undo/Redo: Support for undoing and redoing actions (Ctrl+Z, Ctrl+Y).
Keyboard Navigation: Navigate modes and controls using arrow keys and shortcuts (e.g., Ctrl+S to save).
Modern UI: Collapsible control panels, hover effects, and animations for a polished user experience.

Installation
To run the SVG Path Builder locally:

Clone the Repository:
git clone https://github.com/MUHAMMADUSAMA64874/svg-path-builder-web.git


Navigate to the Project Directory:
cd svg-path-builder-web


Open the Application:

Open index.html in a web browser (e.g., Chrome, Firefox).
Alternatively, serve the files using a local server for better performance:npx http-server

Then navigate to http://localhost:8080 in your browser.



No additional dependencies are required, as the application uses Tailwind CSS via CDN and vanilla JavaScript.
Usage

Access the Application:

Visit the live demo or run locally as described above.


Create a Path:

Select Add Points mode from the "Mode" section and click on the canvas to add points.
Switch to Edit Points mode to drag points or right-click to delete them.


Customize the Path:

Use the "Path" section to adjust path data manually, validate, or load a sample path.
Change colors for the path, endpoints, control points, and handles using the color pickers.


Add Text:

Enter text in the "Text Properties" section, adjust font size, color, letter spacing, and start offset.
Preview text along the path in real-time.


Animate Text:

In the "Animation" section, set the duration and direction, then click "Preview Animation" to see the text move along the path.


Grid and Snapping:

Toggle the grid, adjust its size, or enable snapping in the "Mode" section for precise control.


Import/Export:

Load an image for tracing or an SVG file to edit.
Save the SVG output, copy the SVG code, or fit the path to the canvas.


Toggle Dark Mode:

Use the "Theme" section to switch to dark mode for better visibility in low-light environments.


Keyboard Shortcuts:

Ctrl+Z: Undo
Ctrl+Y: Redo
Ctrl+S: Save SVG
Arrow Keys: Navigate mode dropdown



Contributing
Contributions are welcome! To contribute:

Fork the Repository:

Click the "Fork" button on the GitHub repository.


Create a Branch:
git checkout -b feature/your-feature-name


Make Changes:

Implement your feature or bug fix in the index.html file or related assets.
Ensure the code follows the existing style (e.g., Tailwind CSS, vanilla JavaScript).


Test Locally:

Verify your changes work in both light and dark modes and across browsers.


Commit and Push:
git commit -m "Add your feature description"
git push origin feature/your-feature-name


Create a Pull Request:

Open a pull request on GitHub with a clear description of your changes.



Please include tests or screenshots for significant changes and adhere to the project's coding standards.
License
This project is licensed under the MIT License. Feel free to use, modify, and distribute the code as per the license terms.

Built with ❤️ by MUHAMMADUSAMA64874.
