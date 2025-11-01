/** @odoo-module **/

import { Component, useState, onMounted } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class CameraPreview extends Component {
    static template = "capture_preview_qweb";
    
    setup() {
        this.state = useState({
            mimetype: this.props.action.context.mimetype || "",
            capture_base64String: this.props.action.context.capture_base64String || null,
        });
        
        this.action = useService("action");
        
        // Initialize properties
        this.return_action = this.props.action.return_action;
        this.imagecapture = null;
        this.videocapture = null;
        
        onMounted(() => {
            this.initializePreview();
        });
    }

    initializePreview() {
        // Wait for DOM elements to be available
        setTimeout(() => {
            // Show the camera container
            const cameraMode = document.querySelector('.o_camera_kiosk_mode');
            if (cameraMode) {
                cameraMode.style.display = 'block';
            }
            
            this.imagecapture = document.querySelector("#imagecapture");
            this.videocapture = document.querySelector("#videocapture");
            
            this.displayMedia();
        }, 100);
    }

    displayMedia() {
        if (this.state.mimetype === 'image/jpeg' && this.imagecapture && this.state.capture_base64String) {
            this.imagecapture.src = this.state.capture_base64String;
            this.imagecapture.style.display = 'block';
            if (this.videocapture) {
                this.videocapture.style.display = 'none';
            }
        } else if (this.state.mimetype !== 'image/jpeg' && this.videocapture && this.state.capture_base64String) {
            this.videocapture.setAttribute('controls', '');
            this.videocapture.setAttribute('autoplay', '');
            this.videocapture.setAttribute('muted', '');
            this.videocapture.setAttribute('playsinline', '');
            this.videocapture.src = this.state.capture_base64String;
            this.videocapture.style.display = 'block';
            if (this.imagecapture) {
                this.imagecapture.style.display = 'none';
            }
        }
    }

    onBackButton(ev) {
        ev.preventDefault();
        window.history.back();
    }
}

registry.category("actions").add("capture_show", CameraPreview);