/** @odoo-module **/

import { Component, useState, onMounted, onWillUnmount } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";

export class CameraCapture extends Component {
    static template = "camera_capture_qweb";
    
    setup() {
        this.state = useState({
            mimetype: "",
            capture_base64String: null,
            showControls: 1, // 1: capture mode, 2: preview mode
        });
        
        this.notification = useService("notification");
        this.action = useService("action");
        this.dialog = useService("dialog");
        
        // Initialize properties
        this.res_id = this.props.action.context.res_id;
        this.res_model = this.props.action.context.res_model;
        this.return_action = this.props.action.return_action;
        
        this.canvas = null;
        this.videoElement = null;
        this.wcstream = null;
        this.media_recorder = null;
        this.blobs_recorded = [];
        this.clock_start = null;
        this.capture_image = null;
        this.context = null;
        
        onMounted(() => {
            this.initializeCamera();
        });
        
        onWillUnmount(() => {
            this.destroy();
        });
    }

    async initializeCamera() {
        try {
            const cameraAllowed = await this.checkCamera();
            if (!cameraAllowed) {
                this.action.doAction({ type: 'ir.actions.act_window_close' });
                return;
            }

            // Show the camera container after permission granted
            this.showCameraContainer();
            
            await this.setupCameraElements();
            await this.getStream();
            this.getDevices();
        } catch (error) {
            console.error('Error initializing camera:', error);
            this.action.doAction({ type: 'ir.actions.act_window_close' });
        }
    }

    showCameraContainer() {
        setTimeout(() => {
            const cameraMode = document.querySelector('.o_camera_kiosk_mode');
            if (cameraMode) {
                cameraMode.style.display = 'block';
            }
        }, 100);
    }

    async checkCamera() {
        try {
            // Clean up any existing streams first
            this.cleanupStreams();
            await new Promise(resolve => setTimeout(resolve, 100));
            
            const stream = await navigator.mediaDevices.getUserMedia({ video: true });
            stream.getTracks().forEach(track => {
                track.stop();
                track.enabled = false;
            });
            return true;
        } catch (error) {
            let message = 'An error occurred while accessing the camera: ' + error.message;
            if (error.name === 'NotAllowedError') {
                message = 'Camera access is not allowed. Please enable camera permissions in your browser settings.';
            } else if (error.name === 'NotFoundError') {
                message = 'No camera devices found.';
            } else if (error.name === 'NotReadableError') {
                message = 'Camera is being used by another application. Please close other applications using the camera and try again.';
            }
            alert(message);
            return false;
        }
    }

    setupCameraElements() {
        return new Promise((resolve) => {
            setTimeout(() => {
                this.canvas = document.getElementById('canvas');
                this.audioSelect = document.querySelector('#audioSource');
                this.videoSelect = document.querySelector('#videoSource');
                this.videocapture = document.querySelector("#videocapture");
                this.imagecapture = document.querySelector("#imagecapture");
                this.start_button = document.getElementById("start-record");
                
                if (this.audioSelect) {
                    this.audioSelect.onchange = () => this.getStream();
                }
                if (this.videoSelect) {
                    this.videoSelect.onchange = () => this.getStream();
                }

                this.videoElement = document.createElement('video');
                this.videoElement.setAttribute('autoplay', '');
                this.videoElement.setAttribute('muted', '');
                this.videoElement.setAttribute('playsinline', '');

                this.videoElement.onloadedmetadata = () => {
                    this.videoElement.play();
                    this.capture_image = setInterval(() => {
                        try {
                            if (this.context && this.videoElement && this.canvas) {
                                this.context.drawImage(this.videoElement, 0, 0, this.canvas.width, this.canvas.height);
                            }
                        } catch (error) {
                            // Ignore canvas drawing errors
                        }
                    }, 100);
                };

                this.videoElement.addEventListener('playing', () => {
                    if (this.canvas) {
                        this.canvas.width = this.videoElement.videoWidth;
                        this.canvas.height = this.videoElement.videoHeight;
                        
                        const containerWidth = document.querySelector('.o_camera_kiosk_mode')?.clientWidth || 800;
                        if (this.canvas.width > containerWidth) {
                            const rate = this.canvas.width / containerWidth;
                            this.canvas.width = this.videoElement.videoWidth / rate;
                            this.canvas.height = this.videoElement.videoHeight / rate;
                        }
                        this.context = this.canvas.getContext("2d");
                    }
                }, false);

                this.startClock();
                resolve();
            }, 100);
        });
    }

    async getDevices() {
        try {
            const deviceInfos = await navigator.mediaDevices.enumerateDevices();
            window.deviceInfos = deviceInfos;
            
            deviceInfos.forEach((deviceInfo) => {
                const option = document.createElement('option');
                option.value = deviceInfo.deviceId;
                
                if (deviceInfo.kind === 'audioinput' && this.audioSelect) {
                    option.text = deviceInfo.label || `Microphone ${this.audioSelect.length + 1}`;
                    this.audioSelect.appendChild(option);
                } else if (deviceInfo.kind === 'videoinput' && this.videoSelect) {
                    option.text = deviceInfo.label || `Camera ${this.videoSelect.length + 1}`;
                    this.videoSelect.appendChild(option);
                }
            });
        } catch (error) {
            console.error('Error getting devices:', error);
        }
    }

    async getStream() {
        try {
            // Clean up existing streams more thoroughly
            this.cleanupStreams();

            // Wait a bit for cleanup to complete
            await new Promise(resolve => setTimeout(resolve, 100));

            const audioSource = this.audioSelect?.value;
            const videoSource = this.videoSelect?.value;
            
            // Use more permissive constraints
            const constraints = {
                audio: audioSource ? { deviceId: { exact: audioSource } } : false,
                video: videoSource ? { deviceId: { exact: videoSource } } : true
            };

            const stream = await navigator.mediaDevices.getUserMedia(constraints);
            this.gotStream(stream);
        } catch (error) {
            // Try with more basic constraints if specific device fails
            try {
                this.cleanupStreams();
                await new Promise(resolve => setTimeout(resolve, 100));
                
                const basicConstraints = { video: true, audio: false };
                const stream = await navigator.mediaDevices.getUserMedia(basicConstraints);
                this.gotStream(stream);
            } catch (basicError) {
                alert('Error accessing camera: ' + basicError.message);
            }
        }
    }

    gotStream(stream) {
        window.stream = stream;
        this.wcstream = stream;
        
        if (this.audioSelect && stream.getAudioTracks()[0]) {
            const audioTrack = stream.getAudioTracks()[0];
            this.audioSelect.selectedIndex = [...this.audioSelect.options]
                .findIndex(option => option.text === audioTrack.label);
        }
        
        if (this.videoSelect && stream.getVideoTracks()[0]) {
            const videoTrack = stream.getVideoTracks()[0];
            this.videoSelect.selectedIndex = [...this.videoSelect.options]
                .findIndex(option => option.text === videoTrack.label);
        }
        
        if (this.videoElement) {
            this.videoElement.srcObject = stream;
        }
        
        this.state.showControls = 1;
        this.refresh_control(1);
    }

    onBackButton(ev) {
        ev.preventDefault();
        window.history.back();
    }

    onCaptureButton() {
        if (!this.canvas) return;
        
        this.state.mimetype = 'image/jpeg';
        this.state.capture_base64String = this.canvas.toDataURL('image/jpeg');
        
        if (this.imagecapture) {
            this.imagecapture.src = this.state.capture_base64String;
        }
        
        this.blobs_recorded = [];
        this.state.showControls = 2;
        this.refresh_control(2);

        // Stop the stream after capturing the image
        if (this.wcstream) {
            this.wcstream.getTracks().forEach(track => track.stop());
        }
    }

    onRecordButton() {
        const getSupportedMimeTypes = () => {
            const VIDEO_TYPES = ["webm", "mp4"];
            const VIDEO_CODECS = ["vp9", "vp9.0", "vp8", "vp8.0", "avc1", "av1", "h265", "h.265", "h264", "h.264", "opus"];
            const supportedTypes = [];
            VIDEO_TYPES.forEach((videoType) => {
                const type = `video/${videoType}`;
                if (MediaRecorder.isTypeSupported(type))
                    supportedTypes.push(type);
            });
            return supportedTypes;
        };

        if (this.start_button.innerHTML === 'Video Record') {
            this.blobs_recorded = [];
            this.amimetype = getSupportedMimeTypes();
            const options = (this.amimetype[0] === 'video/mp4') ? {
                audioBitsPerSecond: 12800,
                videoBitsPerSecond: 500000,
                mimeType: this.amimetype[0]
            } : {
                audioBitsPerSecond: 12800,
                mimeType: this.amimetype[0]
            };

            if (this.wcstream) {
                this.media_recorder = new MediaRecorder(this.wcstream, options);
                this.media_recorder.addEventListener('dataavailable', (e) => {
                    this.blobs_recorded.push(e.data);
                });
            } else {
                console.error('Webcam stream not available for recording');
                return;
            }
            
            this.media_recorder.addEventListener('stop', () => {
                console.log("recorder stopped");
                if (this.videocapture && this.canvas) {
                    this.videocapture.width = this.canvas.width;
                    this.videocapture.height = this.canvas.height;
                }
                
                this.state.mimetype = this.amimetype[0];
                const recorded = new Blob(this.blobs_recorded, { 'type': this.amimetype[0] });
                const reader = new FileReader();
                reader.readAsDataURL(recorded);
                reader.onloadend = () => {
                    this.state.capture_base64String = reader.result;
                    if (this.videocapture) {
                        this.videocapture.setAttribute('controls', '');
                        this.videocapture.setAttribute('autoplay', '');
                        this.videocapture.setAttribute('muted', '');
                        this.videocapture.setAttribute('playsinline', '');
                        this.videocapture.src = this.state.capture_base64String;
                    }
                    this.blobs_recorded = [];
                    this.state.showControls = 2;
                    this.refresh_control(2);

                    // Stop the stream after recording the video
                    if (this.wcstream) {
                        this.wcstream.getTracks().forEach(track => track.stop());
                    }
                }
            });
            
            if (this.media_recorder) {
                this.media_recorder.start();
                this.start_button.innerHTML = "Stop Recording";
            }
        } else {
            if (this.media_recorder && this.media_recorder.state !== 'inactive') {
                this.media_recorder.stop();
            }
            this.start_button.innerHTML = "Video Record";
            // Clean up media recorder
            this.media_recorder = null;
        }
    }

    onSaveButton() {
        this.saveCapture();
    }

    async onDeleteButton() {
        // Reset to capture mode
        this.state.showControls = 1;
        this.state.capture_base64String = null;
        this.state.mimetype = "";
        
        // Clean up and reinitialize camera
        this.cleanupStreams();
        await new Promise(resolve => setTimeout(resolve, 200));
        await this.getStream();
    }

    startClock() {
        this.clock_start = setInterval(() => {
            const clockElement = document.querySelector(".o_camera_clock");
            if (clockElement) {
                clockElement.textContent = new Date().toLocaleTimeString(navigator.language, { 
                    hour: '2-digit', 
                    minute: '2-digit', 
                    second: '2-digit' 
                });
                clockElement.style.display = 'block';
            }
        }, 500);
    }

    // Legacy-like visibility controller kept for parity with v16 behavior
    refresh_control(type) {
        const container = document;
        const modeEl = container.querySelector('.o_camera_kiosk_mode');
        if (modeEl) modeEl.style.display = '';

        const show = (sel, visible) => {
            const el = container.querySelector(sel);
            if (el) el.style.display = visible ? '' : 'none';
        };

        if (type === 1) {
            show('#videocapture', false);
            show('#imagecapture', false);
            show('#save-record', false);
            show('#delete-record', false);
            show('#canvas', true);
            show('#start-capture', true);
            show('#start-record', true);
            show('#audioSource', true);
            show('#videoSource', true);
            show('#title_output_device', true);
        } else {
            if (this.state.mimetype === 'image/jpeg') {
                show('#imagecapture', true);
                show('#videocapture', false);
            } else {
                show('#videocapture', true);
                show('#imagecapture', false);
            }
            show('#save-record', true);
            show('#delete-record', true);
            show('#canvas', false);
            show('#start-capture', false);
            show('#start-record', false);
            show('#audioSource', false);
            show('#videoSource', false);
            show('#title_output_device', false);
        }
    }

    async saveCapture() {
        try {
            const note = document.querySelector('#camera_note').value;
            const result = await rpc("/web/dataset/call_kw/ir.attachment/camera_save_capture", {
                model: 'ir.attachment',
                method: 'camera_save_capture',
                args: [this.res_model, this.res_id, this.state.capture_base64String, this.state.mimetype, note],
                kwargs: {}
            });

            if (result.warning) {
                this.notification.add(result.warning, {
                    type: 'danger',
                    title: 'Save Error',
                });
            } else {
                this.notification.add(result.result || 'Image saved successfully!', {
                    type: 'success',
                    title: 'Save Success',
                });
                this.state.showControls = 1;
                this.state.capture_base64String = null;
                this.state.mimetype = "";
                await this.getStream();
            }
        } catch (error) {
            this.notification.add('Error saving capture: ' + error.message, {
                type: 'danger',
                title: 'Save Error',
            });
        }
    }

    cleanupStreams() {
        // Clean up current stream
        if (this.wcstream) {
            this.wcstream.getTracks().forEach(track => {
                track.stop();
                track.enabled = false;
            });
            this.wcstream = null;
        }
        
        // Clean up window.stream
        if (window.stream) {
            window.stream.getTracks().forEach(track => {
                track.stop();
                track.enabled = false;
            });
            window.stream = null;
        }
        
        // Clear video element source
        if (this.videoElement) {
            this.videoElement.srcObject = null;
        }
    }

    destroy() {
        if (this.clock_start) {
            clearInterval(this.clock_start);
        }
        if (this.capture_image) {
            clearInterval(this.capture_image);
        }
        this.cleanupStreams();
    }

    getCurrentTime() {
        return new Date().toLocaleTimeString(navigator.language, { 
            hour: '2-digit', 
            minute: '2-digit', 
            second: '2-digit' 
        });
    }
}

registry.category("actions").add("camera_capture", CameraCapture);