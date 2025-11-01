{
    "name": "Capture Delivery Image | Camera Capture | Stock Picking Image | Delivery Proof | Camera Delivery | Image Capture | Delivery Image Capture",
    "summary": "Capture and attach images to delivery records for proof of delivery and quality control",
    "description": """
        📸 **Image Capture for Delivery Management in Odoo 18**
        
        Enhance your delivery process with visual proof! This powerful module allows you to capture and attach images directly to stock picking records, providing essential documentation for delivery verification and quality control.
        
        **✨ Key Features:**
        
        📷 **Camera Integration**
        - Direct camera capture from delivery forms
        - High-quality image capture with device camera
        - Real-time image preview before saving
        - Support for multiple image formats
        
        🚚 **Delivery Management**
        - Attach images to stock picking records
        - Visual proof of delivery completion
        - Timestamped image capture with timezone support
        - Easy image viewing and management
        
        📝 **Smart Documentation**
        - Automatic filename generation with timestamps
        - Optional note attachment with images
        - UTC timezone support for global operations
        - Organized image storage in attachments
        
        🔧 **Technical Features**
        - Odoo 18 compatible
        - Responsive camera interface
        - Base64 image encoding
        - Secure image storage
        - Performance optimized
        
        🎯 **Perfect For:**
        - Delivery companies needing proof of delivery
        - Quality control departments
        - Field service operations
        - Inventory management with visual verification
        - Customer service with delivery confirmation
        
        **💡 Use Cases:**
        - Capture delivery completion photos
        - Document package condition upon delivery
        - Record delivery location and context
        - Provide visual proof for customer disputes
        - Maintain delivery quality standards
        
        **🔧 Technical Implementation:**
        - Seamless integration with stock picking workflow
        - Custom camera capture interface
        - Automatic attachment management
        - Timezone-aware timestamping
        - Clean, modern user interface
        
        Transform your delivery process with visual documentation!
    """,
    "version": "0.1.0",
    "category": "Inventory/Delivery",
    'author': "Mountain Tran",
    'support': "mountaintran2021@gmail.com",
'website': "https://mountain-coder.com",
    'license': 'OPL-1',
    'price': 15,
    'currency': 'EUR',
    "depends": ["stock","car_repair_industry"],
    'images': [
        'static/description/banner.png',
        'static/description/icon.png',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'data': [
        'views/stock_picking_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'ta_capture_delivery_image/static/src/**/*',
        ],
    },
}

