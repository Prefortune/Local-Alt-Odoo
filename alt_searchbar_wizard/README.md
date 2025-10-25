# Alt Searchbar Wizard

A dynamic, configurable searchbar component for Odoo 18 websites.

## Features

- **Dynamic Configuration**: Each website can define its own searchbar structure
- **Bootstrap 5 Styling**: Fully responsive with theme support
- **Multi-website Support**: Separate configurations per website
- **SEO Optimized**: Clean URLs and proper meta tags
- **No Custom CSS**: Uses Bootstrap 5 classes and CSS variables only

## Installation

1. Copy the module to your Odoo addons directory
2. Update the addons list in Odoo
3. Install the module from Apps menu

## Usage

### For Website Administrators

1. Go to `Website > Configuration > Searchbar Settings`
2. Create a new configuration for your website
3. Select categories and attributes to include
4. Enable/disable price filter as needed
5. Save and activate the configuration

### For Content Editors

Since snippets are not automatically available in Odoo 18, you can add the searchbar to any page by:

1. **Method 1: Add HTML directly**
   ```html
   <div id="searchbar_wrapper" class="searchbar-container">
       <!-- Dynamic content will be loaded here -->
   </div>
   ```

2. **Method 2: Use the template in custom pages**
   ```xml
   <t t-call="alt_searchbar_wizard.alt_searchbar_snippet"/>
   ```

3. **Method 3: Add via Website Builder**
   - Edit any page in Website Builder
   - Add a custom HTML block
   - Insert the wrapper div with id="searchbar_wrapper"

### For Developers

- The search bar automatically loads the correct configuration for the current website
- All styling is handled by Bootstrap 5 classes and CSS variables
- No additional CSS required - fully theme-compatible

## Technical Details

### Model: `alt.searchbar.config`

- `name`: Internal name for the configuration
- `website_id`: Website this configuration belongs to
- `category_ids`: Product categories to include
- `attribute_ids`: Product attributes to include
- `show_price_filter`: Whether to include price min/max fields
- `is_active`: Whether this configuration is active

### Controller Routes

- `/alt/searchbar/config`: JSON endpoint to get configuration
- `/shop`: Handles search form submission

### JavaScript

- `searchbar_loader.js`: Loads configuration and renders searchbar
- Uses publicWidget for frontend integration
- Error handling with fallback to default searchbar

## Requirements

- Odoo 18.0
- website_sale module
- Bootstrap 5 (included with Odoo 18)

## License

LGPL-3 