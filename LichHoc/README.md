# EduSchedule - Lịch học (Schedule Page)

This is an implementation of a class schedule page for the EduLearn online learning system based on a Figma design.

## Project Structure

- `index.html` - The HTML structure of the schedule page
- `styles.css` - CSS styling for the page
- `script.js` - JavaScript functionality for the page
- `assets/` - Directory containing SVG icons from the design

## Features

- Clean, modern user interface
- Navigation sidebar with page links
- Monthly calendar view with class events
- Upcoming classes section with details and "Enter Class" buttons
- Responsive design that adapts to different screen sizes
- Interactive elements with hover effects and click functionality

## Implementation Details

### HTML Structure

The HTML is organized with semantic markup:
- Header with logo and user profile
- Sidebar navigation
- Main content area with:
  - Monthly calendar section
  - Upcoming classes section

### CSS Styling

The CSS implements:
- Responsive grid-based calendar layout
- Card-based design for components
- Subtle shadows and borders for depth
- Adaptive layouts for different screen sizes
- Interactive hover and active states

### JavaScript Functionality

The JavaScript provides:
- Navigation between sidebar items
- Month navigation in the calendar
- Click events for calendar days with classes
- "Enter Class" button functionality
- User profile and notification interactions

## Responsive Design

The page is fully responsive and works well on:
- Desktop computers
- Tablets
- Mobile phones

On smaller screens, the layout adapts:
- Sidebar becomes a horizontal navigation bar
- Calendar cells adjust in size
- Class cards stack vertically

## How to Use

1. Make sure all files are in the same directory structure as provided
2. Open `index.html` in a web browser
3. Interact with the navigation, calendar, and class buttons

## Design Source

This implementation is based on the Figma design at:
[https://www.figma.com/design/LLQEq95BrRBahKn0RTWjNU/online_learning_system](https://www.figma.com/design/LLQEq95BrRBahKn0RTWjNU/online_learning_system?node-id=5-800&t=kK8OizwFcJZjLLQB-1)

## Notes

This is a frontend implementation only. In a real application, the calendar data and class information would be fetched from a backend API. The "Enter Class" buttons would connect to a virtual classroom system. 